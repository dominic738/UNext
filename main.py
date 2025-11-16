
from fastapi.middleware.cors import CORSMiddleware


import os
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import cosine_similarity
from math import radians, cos, sin, asin, sqrt

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()



app = FastAPI(title="College Match API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



class HybridCollegeMatcher:
    """
    Hybrid recommender:
      - PCA + cosine similarity on curated numeric features
      - Plus explicit subscores for affordability, academics, fit, diversity/mobility, distance
      - Final score is a weighted combination using student preferences.
    """

    def __init__(self, curated_features, weights=None, n_components=20,
                 max_distance_km=3500, cc_penalty=0.55):
        self.curated_features = curated_features
        self.weights = weights if weights else {}
        self.n_components = n_components
        self.max_distance_km = max_distance_km
        self.cc_penalty = cc_penalty

        self.scaler = None
        self.pca = None
        self.numeric_features = None
        self.college_embeddings = None
        self.df_full = None
        self.medians = None

    
    def haversine(self, lat1, lon1, lat2, lon2):
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        return 6371 * 2 * asin(sqrt(a))  # km

    
    def add_engineered_features(self, df):
        race_cols = [
            "Percent of White Undergraduates",
            "Percent of Black or African American Undergraduates",
            "Percent of Latino Undergraduates",
            "Percent of Asian Undergraduates",
            "Percent of American Indian or Alaska Native Undergraduates",
            "Percent of Native Hawaiian or Other Pacific Islander Undergraduates",
            "Percent of Two or More Races Undergraduates",
        ]
        race_cols = [c for c in race_cols if c in df.columns]

        if race_cols:
            race_props = df[race_cols].div(100)

            def entropy(row):
                p = row[row > 0]
                return -(p * np.log(p)).sum() if len(p) else 0.0

            df["diversity_entropy"] = race_props.apply(entropy, axis=1)
        else:
            df["diversity_entropy"] = 0.0

        
        if "Number of Bachelor Degrees Grand Total" in df.columns:
            total = df["Number of Bachelor Degrees Grand Total"].replace(0, np.nan)

            share_map = {
                "Number of Degrees Awarded in Science, Technology, Engineering, and Math": "stem_share",
                "Number of Degrees Awarded in Business": "business_share",
                "Number of Degrees Awarded in Health Sciences": "health_share",
                "Number of Degrees Awarded in Arts and Humanities": "arts_share",
                "Number of Degrees Awarded in Education": "education_share",
                "Number of Degrees Awarded in Social Sciences": "soc_science_share",
            }
            for src, tgt in share_map.items():
                if src in df.columns and tgt not in df.columns:
                    df[tgt] = (df[src] / total).fillna(0)
        else:
            for c in ["stem_share", "business_share", "health_share",
                      "arts_share", "education_share", "soc_science_share"]:
                df[c] = df.get(c, 0.0)

        return df.fillna(0)

    # ------------------- Fit Function ---------------------
    def fit(self, df_full):
        df_full = df_full.copy()
        df_full = self.add_engineered_features(df_full)

        self.df_full = df_full

        FEATURES = [c for c in self.curated_features if c in df_full.columns]
        numeric_cols = df_full.select_dtypes(include=[np.number]).columns
        self.numeric_features = [c for c in FEATURES if c in numeric_cols]

        self.medians = df_full[self.numeric_features].median()
        X = df_full[self.numeric_features].fillna(self.medians)

        for col, w in self.weights.items():
            if col in X.columns:
                X[col] *= w

        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        self.pca = PCA(n_components=min(self.n_components, len(self.numeric_features)))
        self.college_embeddings = self.pca.fit_transform(X_scaled)

        self.df_full["embedding"] = list(self.college_embeddings)
        return self

    # ---------------- Prefs -------------------
    def _build_student_prefs(self, student):
        prefs = {
            "importance_afford": student.get("importance_afford", 0.4),
            "importance_outcomes": student.get("importance_outcomes", 0.3),
            "importance_diversity": student.get("importance_diversity", 0.2),
            "importance_mobility": student.get("importance_mobility", 0.2),
            "importance_location": student.get("importance_location", 0.2),
        }

        total = sum(prefs.values())
        if total > 0:
            prefs = {k: v / total for k, v in prefs.items()}

        prefs["importance_similarity"] = 0.2
        rem = 0.8
        non_sim_total = sum(v for k, v in prefs.items() if k != "importance_similarity")

        for k in prefs:
            if k != "importance_similarity":
                prefs[k] = prefs[k] * rem / non_sim_total

        return prefs

    # ---------------- Distance -------------------
    def _compute_distances(self, student, df):
        lat = student.get("home_lat")
        lon = student.get("home_lon")

        if lat is None or lon is None:
            return pd.Series(np.nan, index=df.index)

        return pd.Series([
            self.haversine(lat, lon, a, b)
            for a, b in zip(df["Latitude"], df["Longitude"])
        ], index=df.index)

    # ---------------- Affordability -------------------
    def _score_affordability(self, student, df):
        target_price = student.get("target_net_price", 15000)
        will_work = student.get("will_work_job", True)
        max_hours = student.get("max_work_hours", 10)

        if "Net Price" in df.columns:
            price = df["Net Price"].clip(lower=0)
        else:
            price = pd.Series(target_price, index=df.index)

        ratio = price / max(target_price, 1)
        price_score = np.clip(2.0 - ratio, 0, 1) * 100

        hrs_cols = [
            "Weekly Hours to Close Gap",
            "Weekly Hours to Close Gap: Center-Based Care",
            "Weekly Hours to Close Gap: Home-Based Care",
        ]
        hrs_cols = [c for c in hrs_cols if c in df.columns]

        if hrs_cols and will_work:
            hrs = df[hrs_cols[0]].fillna(max_hours)
            hrs_score = np.clip(2.0 - hrs / max(max_hours, 1), 0, 1) * 100
            return 0.7 * price_score + 0.3 * hrs_score

        return price_score

    # ---------------- Distance Score -------------------
    def _score_distance(self, dist):
        score = (1 - dist / self.max_distance_km) * 100
        return score.clip(0, 100).fillna(70)

    # ---------------- Academics -------------------
    def _score_academics(self, student, df):
        sat = student.get("sat_score", None)

        if "Bachelor's Degree Graduation Rate Bachelor Degree Within 6 Years - Total" in df.columns:
            grad = df["Bachelor's Degree Graduation Rate Bachelor Degree Within 6 Years - Total"].fillna(0) / 100
        else:
            grad = pd.Series(0.5, index=df.index)

        if "First-Time, Full-Time Retention Rate" in df.columns:
            retain = df["First-Time, Full-Time Retention Rate"].fillna(0) / 100
        else:
            retain = pd.Series(0.5, index=df.index)

        if sat is not None and \
           "SAT Evidence Based Reading and Writing - 25th Percentile Score" in df.columns and \
           "SAT Evidence Based Reading and Writing - 75th Percentile Score" in df.columns:

            sat25 = df["SAT Evidence Based Reading and Writing - 25th Percentile Score"].fillna(0)
            sat75 = df["SAT Evidence Based Reading and Writing - 75th Percentile Score"].fillna(0)

            alignment = []
            for s25, s75 in zip(sat25, sat75):
                if s25 <= 0:
                    alignment.append(0.6)
                elif sat < s25:
                    alignment.append(max(0, sat / s25 * 0.8))
                elif sat > s75:
                    alignment.append(0.9)
                else:
                    alignment.append(1.0)
            align = pd.Series(alignment, index=df.index)
        else:
            align = pd.Series(0.8, index=df.index)

        return (0.5 * grad + 0.3 * retain + 0.2 * align) * 100

    # ---------------- Diversity + Mobility -------------------
    def _score_diversity_mobility(self, student, df):
        imp_div = student.get("importance_diversity", 0)
        imp_mob = student.get("importance_mobility", 0)
        eth = (student.get("self_race", "") or "").lower()

        if "diversity_entropy" in df.columns:
            div_norm = (df["diversity_entropy"] / df["diversity_entropy"].max()).clip(0, 1)
        else:
            div_norm = pd.Series(0.5, index=df.index)

        if "Percent of First-Time, Full-Time Undergraduates Awarded Pell Grants" in df.columns:
            pell = df["Percent of First-Time, Full-Time Undergraduates Awarded Pell Grants"].fillna(0) / 100
        else:
            pell = pd.Series(0.5, index=df.index)

        msi = pd.Series(0.0, index=df.index)
        if eth:
            if "latino" in eth and "HSI" in df.columns:
                msi += df["HSI"].fillna(0) * 0.2
            if ("black" in eth or "african" in eth) and "HBCU" in df.columns:
                msi += df["HBCU"].fillna(0) * 0.25

        score = (imp_div * div_norm * 100 + imp_mob * pell * 100) / max(imp_div + imp_mob, 1e-6)
        return (score + msi * 100).clip(0, 100)

    # ---------------- Fit Score -------------------
    def _score_fit(self, student, df):
        intended = (student.get("intended_major", "") or "").lower()
        major_map = {
            "stem": "stem_share",
            "science": "stem_share",
            "engineering": "stem_share",
            "business": "business_share",
            "health": "health_share",
            "nursing": "health_share",
            "arts": "arts_share",
            "humanities": "arts_share",
            "education": "education_share",
            "social": "soc_science_share",
            "social science": "soc_science_share",
        }

        if intended in major_map and major_map[intended] in df.columns:
            major_fit = df[major_map[intended]].fillna(0)
        else:
            major_fit = pd.Series(0.5, index=df.index)

        size_pref = student.get("pref_size", None)
        size_map = {"small": 1, "medium": 2, "large": 3}
        size_pref_num = size_map.get(size_pref, None) if isinstance(size_pref, str) else size_pref

        if "Institution Size Category" in df.columns and size_pref_num is not None:
            size_diff = (df["Institution Size Category"] - size_pref_num).abs()
            size_score = np.clip(1 - 0.3 * size_diff, 0, 1)
        else:
            size_score = pd.Series(0.7, index=df.index)

        sector_pref = (student.get("pref_sector", "") or "").lower()
        sector_map = {"public": 1, "private": 2}
        sector_pref_num = sector_map.get(sector_pref, None)

        if "Control of Institution" in df.columns and sector_pref_num is not None:
            sec_diff = (df["Control of Institution"] - sector_pref_num).abs()
            sec_score = np.clip(1 - 0.5 * sec_diff, 0, 1)
        else:
            sec_score = pd.Series(0.7, index=df.index)

        return (0.5 * major_fit + 0.25 * size_score + 0.25 * sec_score) * 100

    # ---------------- Similarity -------------------
    def _score_similarity(self, student):
        row = self.medians.copy()

        target_price = student.get("target_net_price", None)
        if target_price is not None and "Net Price" in row:
            row["Net Price"] = target_price

        intended = (student.get("intended_major", "") or "").lower()
        major_map = {
            "stem": "stem_share",
            "business": "business_share",
            "health": "health_share",
            "arts": "arts_share",
            "education": "education_share",
            "social": "soc_science_share",
        }
        if intended in major_map and major_map[intended] in row:
            col = major_map[intended]
            row[col] = row[col] * 2.0

        imp_out = student.get("importance_outcomes", 0)
        if imp_out > 0:
            for c in [
                "Bachelor's Degree Graduation Rate Bachelor Degree Within 6 Years - Total",
                "First-Time, Full-Time Retention Rate",
                "Median Earnings of Students Working and Not Enrolled 10 Years After Entry",
            ]:
                if c in row.index:
                    row[c] *= (1 + 0.5 * imp_out)

        student_vec = pd.DataFrame([row[self.numeric_features]])

        for col, w in self.weights.items():
            if col in student_vec.columns:
                student_vec[col] *= w

        scaled = self.scaler.transform(student_vec)
        emb = self.pca.transform(scaled)

        sims = cosine_similarity(self.college_embeddings, emb).flatten()
        return ((sims + 1) / 2) * 100

    # ---------------- MATCH -------------------
    def match(self, student, top_k=10, return_components=False):
        if self.df_full is None:
            raise ValueError("Call fit(df_full) first.")

        prefs = self._build_student_prefs(student)

        df = self.df_full.copy()

        df["Institution Name"] = df["Institution Name"].astype(str)

        
        if "Number of Bachelor Degrees Grand Total" in df.columns:
            df = df[df["Number of Bachelor Degrees Grand Total"] >= 200]

        INVALID = [
            "Cosmetology", "Beauty", "Barber", "Massage", "Therapy",
            "Academy", "Institute", "Technical", "Vocational", "Career",
            "Truck", "Trucking", "Driving", "Motorcycle",
            "Culinary", "Cooking", "HVAC", "Welding",
            "Seminary", "Ministry", "Bible", "Theological"
        ]

        pattern = "|".join(INVALID)
        df = df[~df["Institution Name"].str.contains(pattern, case=False, na=False)]

        # ---------------- No For Profit Schools -------------------
        if "Control of Institution" in df.columns:
            df = df[df["Control of Institution"] != 3]

        if "First-Time, Full-Time Retention Rate" in df.columns:
            df = df[df["First-Time, Full-Time Retention Rate"] >= 62]

        if "Bachelor's Degree Graduation Rate Bachelor Degree Within 6 Years - Total" in df.columns:
            df = df[df["Bachelor's Degree Graduation Rate Bachelor Degree Within 6 Years - Total"] >= 40]

        required_cols = [
            "Net Price",
            "First-Time, Full-Time Retention Rate",
            "Bachelor's Degree Graduation Rate Bachelor Degree Within 6 Years - Total",
            "Median Earnings of Students Working and Not Enrolled 10 Years After Entry",
        ]
        for col in required_cols:
            if col in df.columns:
                df = df[df[col].notna() & (df[col] > 0)]

        if "Median Earnings of Students Working and Not Enrolled 10 Years After Entry" in df.columns:
            df = df[df["Median Earnings of Students Working and Not Enrolled 10 Years After Entry"] >= 35000]

        if student.get("intended_major", "").lower() == "stem":
            if "stem_share" in df.columns:
                df = df[df["stem_share"] >= 0.10]

        # DISTANCE
        dist = self._compute_distances(student, df)
        df["distance_km"] = dist
        df = df[dist.isna() | (dist <= self.max_distance_km)]
        dist = df["distance_km"]

        # SCORES
        afford = self._score_affordability(student, df)
        acad = self._score_academics(student, df)
        divmob = self._score_diversity_mobility(student, df)
        fit = self._score_fit(student, df)
        dist_score = self._score_distance(dist)
        sim_full = self._score_similarity(student)
        sim = pd.Series(sim_full, index=self.df_full.index).loc[df.index]

        final = (
            prefs["importance_afford"] * afford +
            prefs["importance_outcomes"] * acad +
            prefs["importance_diversity"] * divmob +
            prefs["importance_mobility"] * divmob +
            prefs["importance_location"] * dist_score +
            prefs["importance_similarity"] * sim
        )

        df["match_score"] = final.clip(0, 100)

        df = df.sort_values("match_score", ascending=False)
        df = df.drop_duplicates(subset=["Institution Name"])

        comp = {
            "afford_score": afford,
            "academic_score": acad,
            "diversity_mobility_score": divmob,
            "fit_score": fit,
            "distance_score": dist_score,
            "similarity_score": sim,
        }

        for name, vals in comp.items():
            df[name] = vals

        df_top = df.head(min(top_k, 5)).copy()

        api_key = os.getenv("OPENAI_API_KEY")
        if api_key is None:
            raise ValueError("OPENAI_API_KEY not found.")

        client = OpenAI(api_key=api_key)

        rationales = []

        for _, row in df_top.iterrows():
            prompt = f"""
        You are assisting a student in choosing colleges.

        Student profile:
        {student}

        College:
        - Name: {row['Institution Name']}
        - Match score: {row['match_score']:.1f}
        - Affordability score: {row['afford_score']:.1f}
        - Academic score: {row['academic_score']:.1f}
        - Fit score: {row['fit_score']:.1f}
        - Diversity/Mobility score: {row['diversity_mobility_score']:.1f}
        - Distance score: {row['distance_score']:.1f}
        - Similarity score: {row['similarity_score']:.1f}

        Write 4-5 clear sentences explaining why this school is a good match using this data.
        The goal is to democratize access to high-quality advice and guide students, 
        especially from vulnerable populations, 
        toward institutions that offer high value, 
        low debt, and a strong record of equitable outcomes.
        """

            try:
                resp = client.chat.completions.create(
                    model="gpt-4.1-mini",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=200,
                )
                rationale = resp.choices[0].message.content
            except Exception as e:
                rationale = "Rationale unavailable."

            rationales.append(rationale)

        df_top["rationale"] = rationales

        return df_top[
            ["Institution Name", "match_score", "Net Price", "distance_km", "rationale"]
        ]


# ----------------------------------------------------------------------
#  FASTAPI BACKEND
# ----------------------------------------------------------------------


DATA_LOADED = False
matcher = None
df_full = None


# ----- Pydantic model -----
class StudentRequest(BaseModel):
    target_net_price: Optional[float] = 15000
    max_work_hours: Optional[int] = 15
    family_income: Optional[int] = 50000

    importance_afford: Optional[float] = 0.4
    importance_outcomes: Optional[float] = 0.3
    importance_diversity: Optional[float] = 0.2
    importance_mobility: Optional[float] = 0.2
    importance_location: Optional[float] = 0.2

    sat_score: Optional[int] = None
    act_score: Optional[int] = None

    self_race: Optional[str] = None
    will_work_job: Optional[bool] = True

    pref_sector: Optional[str] = None
    pref_size: Optional[str] = None

    home_lat: Optional[float] = None
    home_lon: Optional[float] = None

    intended_major: Optional[str] = None


# ----- Dataset Loading -----
def load_datasets():
    """Loads and merges the datasets + initializes the matcher."""
    global df_full, matcher, DATA_LOADED

    if DATA_LOADED:
        return True

    print("Loading datasets...")

    try:
        df_afford = pd.read_excel("data/Affordability Gap Data AY2022-23 2.17.25.xlsx")
        df_results = pd.read_excel("data/College Results View 2021 Data Dump for Export.xlsx")
    except Exception as e:
        print("Dataset loading error:", e)
        return False

    df = df_afford.merge(
        df_results,
        left_on="Unit ID",
        right_on="UNIQUE_IDENTIFICATION_NUMBER_OF_THE_INSTITUTION",
        how="inner"
    )

    total = df["Number of Bachelor Degrees Grand Total"].replace(0, np.nan)

    engineered = pd.DataFrame({
        "stem_share": df["Number of Degrees Awarded in Science, Technology, Engineering, and Math"] / total,
        "business_share": df["Number of Degrees Awarded in Business"] / total,
        "health_share": df["Number of Degrees Awarded in Health Sciences"] / total,
        "arts_share": df["Number of Degrees Awarded in Arts and Humanities"] / total,
        "education_share": df["Number of Degrees Awarded in Education"] / total,
        "soc_science_share": df["Number of Degrees Awarded in Social Sciences"] / total
    }).fillna(0)

    df = pd.concat([df, engineered], axis=1)

    df = df.rename(columns={"Institution Name_x": "Institution Name"})
    df = df.drop(columns=["Institution Name_y"], errors="ignore")

    for col in df.select_dtypes(include=[np.number]).columns:
        df[col] = df[col].fillna(df[col].median())

    # Import curated features + weights
    from backend_feature_config import CURATED_FEATURES, weights

    df_full = df.copy()

    matcher = HybridCollegeMatcher(
        curated_features=CURATED_FEATURES,
        weights=weights,
        n_components=20,
        max_distance_km=3500
    )

    matcher.fit(df_full)
    DATA_LOADED = True
    print("Model ready.")
    return True


# ----------------------------------------------------------------------
#  ENDPOINTS
# ----------------------------------------------------------------------

@app.get("/")
def home():
    return {"message": "College Match API is running!"}


@app.post("/match")
def match_colleges(student: StudentRequest):
    ok = load_datasets()
    if not ok:
        raise HTTPException(status_code=500, detail="Dataset error")

    student_dict = student.dict(exclude_none=True)

    try:
        result = matcher.match(student_dict)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return result.to_dict(orient="records")

