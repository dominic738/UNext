
afford_cols = [
    "Net Price",
    "Affordability Gap (net price minus income earned working 10 hrs at min wage)",
    "Weekly Hours to Close Gap",
    "100% TTD Affordability Gap",
    "150% TTD Affordability Gap",
    "Average Work Study Award",
    "Student Parent Affordability Gap: Center-Based Care",
    "Student Parent Affordability Gap: Home-Based Care",
    "Weekly Hours to Close Gap: Center-Based Care",
    "Weekly Hours to Close Gap: Home-Based Care",
    "Adjusted Annual Center-Based Child Care Cost",
    "Adjusted Annual Home-Based Child Care Cost",
    "Cost of Attendance: Out of State",
    "Cost of Attendance: In State"
]

academic_cols = [
    "Bachelor's Degree Graduation Rate Within 4 Years - Total",
    "Bachelor's Degree Graduation Rate Bachelor Degree Within 6 Years - Total",
    "Bachelor's Degree Graduation Rate Bachelor Degree Within 6 Years - Women",
    "Bachelor's Degree Graduation Rate Within 6 Years - Men",
    "Bachelor's Degree Graduation Rate Within 6 Years - Black, Non-Latino",
    "Bachelor's Degree Graduation Rate Within 6 Years - Latino",
    "Bachelor's Degree Graduation Rate Within 6 Years - Asian",
    "Bachelor's Degree Graduation Rate Within 6 Years - White Non-Latino",
    "Transfer Out Rate",
    "First-Time, Full-Time Retention Rate",
    "Student-to-Faculty Ratio",
    "Total Percent of Applicants Admitted",
    "SAT Evidence Based Reading and Writing - 25th Percentile Score",
    "SAT Evidence Based Reading and Writing - 75th Percentile Score",
    "SAT Math - 25th Percentile Score",
    "SAT Math - 75th Percentile Score",
    "ACT English - 25th Percentile Score",
    "ACT English - 75th Percentile Score",
    "ACT Math - 25th Percentile Score",
    "ACT Math - 75th Percentile Score",
    "Instructional Expenses Per FTE",
    "Instructional Expenses GASB Per Student",
    "Instructional Expenses FASB Per FTE"
]

economic_cols = [
    "Median Earnings of Students Working and Not Enrolled 10 Years After Entry",
    "Median Earnings of Dependent Students Working and Not Enrolled 10 Years After Entry",
    "Median Earnings of Independent Students Working and Not Enrolled 10 Years After Entry",
    "Median Debt for Dependent Students",
    "Median Debt for Independent Students",
    "Median Debt of Completers",
    "Cohort Default Rate",
    "Percent of First-Time, Full-Time Undergraduates Awarded Pell Grants",
]

demo_cols = [
    "Percent of White Undergraduates",
    "Percent of Black or African American Undergraduates",
    "Percent of Latino Undergraduates",
    "Percent of Asian Undergraduates",
    "Percent of American Indian or Alaska Native Undergraduates",
    "Percent of Native Hawaiian or Other Pacific Islander Undergraduates",
    "Percent of Two or More Races Undergraduates",
    "Percent of Women Undergraduates",
    "Percent of Men Undergraduates",
    "Percent of Undergraduates Age 25 to 64",
    "Percent of Undergraduates Enrolled Exclusively in Distance Education Courses",
    "Total Enrollment",
]


degree_cols = [
    "Number of Degrees Awarded in Science, Technology, Engineering, and Math",
    "Number of Degrees Awarded in Arts and Humanities",
    "Number of Degrees Awarded in Education",
    "Number of Degrees Awarded in Social Sciences",
    "Number of Degrees Awarded in Health Sciences",
    "Number of Degrees Awarded in Business",
]


location_cols = [
    "Latitude",
    "Longitude",
    "Region #",
    "Degree of Localization",         
    "Institution Size Category",      
    "Control of Institution",         
]

msi_cols = [
    "HBCU",
    "HSI",
    "AANAPII",
    "PBI",
    "NANTI",
    "ANNHI",
    "TRIBAL",
]

CURATED_FEATURES = (
    afford_cols +
    academic_cols +
    economic_cols +
    demo_cols +
    degree_cols +
    location_cols +
    msi_cols +
    [
        "stem_share", "business_share", "health_share",
        "arts_share", "education_share", "soc_science_share"
    ]
)


weights = {

    # ------------------------------------------------------------
    # 1. AFFORDABILITY
    # ------------------------------------------------------------
    "Net Price": 2.5,
    "Affordability Gap (net price minus income earned working 10 hrs at min wage)": 2.2,
    "Weekly Hours to Close Gap": 2.0,
    "100% TTD Affordability Gap": 1.2,
    "150% TTD Affordability Gap": 1.2,
    "Average Work Study Award": 1.0,
    "Student Parent Affordability Gap: Center-Based Care": 1.8,
    "Student Parent Affordability Gap: Home-Based Care": 1.6,
    "Weekly Hours to Close Gap: Center-Based Care": 1.4,
    "Weekly Hours to Close Gap: Home-Based Care": 1.4,

    # Housing/COA
    "Cost of Attendance: In State": 1.6,
    "Cost of Attendance: Out of State": 1.4,
    

    # ------------------------------------------------------------
    # 2. ACADEMICS
    # ------------------------------------------------------------
    "Bachelor's Degree Graduation Rate Bachelor Degree Within 6 Years - Total": 2.0,
    "First-Time, Full-Time Retention Rate": 1.7,
    "Student-to-Faculty Ratio": 1.2,

    
    "SAT Evidence Based Reading and Writing - 25th Percentile Score": 1.0,
    "SAT Evidence Based Reading and Writing - 75th Percentile Score": 1.0,
    "SAT Math - 25th Percentile Score": 1.0,
    "SAT Math - 75th Percentile Score": 1.0,

    "ACT English - 25th Percentile Score": 1.0,
    "ACT English - 75th Percentile Score": 1.0,
    "ACT Math - 25th Percentile Score": 1.0,
    "ACT Math - 75th Percentile Score": 1.0,


    # ------------------------------------------------------------
    # 3. ECONOMIC OUTCOMES
    # ------------------------------------------------------------
    "Median Earnings of Students Working and Not Enrolled 10 Years After Entry": 1.7,
    "Median Debt of Completers": 1.4,
    "Median Debt for Dependent Students": 1.2,
    "Median Debt for Independent Students": 1.2,
    "Cohort Default Rate": 1.4,
    "Percent of First-Time, Full-Time Undergraduates Awarded Pell Grants": 1.0,


    # ------------------------------------------------------------
    # 4. DEMOGRAPHICS + DIVERSITY
    # ------------------------------------------------------------
    "Percent of White Undergraduates": 0.6,
    "Percent of Black or African American Undergraduates": 0.9,
    "Percent of Latino Undergraduates": 0.9,
    "Percent of Asian Undergraduates": 0.7,
    "Percent of American Indian or Alaska Native Undergraduates": 0.9,
    "Percent of Native Hawaiian or Other Pacific Islander Undergraduates": 0.9,
    "Percent of Two or More Races Undergraduates": 0.8,

    "Percent of Women Undergraduates": 0.4,
    "Percent of Men Undergraduates": 0.4,

    # Nontraditional
    "Percent of Undergraduates Age 25 to 64": 0.7,
    "Percent of Undergraduates Enrolled Exclusively in Distance Education Courses": 0.4,


    # ------------------------------------------------------------
    # 5. DEGREE FIELDS / MAJOR ALIGNMENT
    # ------------------------------------------------------------
    "stem_share": 2.0,
    "business_share": 2.0,
    "health_share": 2.0,
    "arts_share": 2.0,
    "education_share": 2.0,
    "soc_science_share": 2.0,


    # ------------------------------------------------------------
    # 6. LOCATION & MISSION
    # ------------------------------------------------------------
    "Latitude": 0.2,
    "Longitude": 0.2,
    "Region #": 0.3,
    "Degree of Localization": 0.5,
    "Institution Size Category": 0.5,
    "Control of Institution": 0.6,

    # MSI categories
    "HBCU": 1.4,
    "HSI": 1.2,
    "AANAPII": 1.0,
    "PBI": 1.3,
    "NANTI": 1.3,
    "ANNHI": 1.2,
    "TRIBAL": 1.3
}
