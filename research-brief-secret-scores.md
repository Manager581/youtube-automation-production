# RESEARCH BRIEF: "The Secret Score That Controls Your Life (It's Not Your Credit Score)"

## Executive Summary
Landlords, employers, and insurers use opaque algorithmic scores -- compiled from shopping habits, social media, neighborhood demographics, and more -- to decide who gets apartments, jobs, and coverage. Consumers cannot see, understand, or dispute most of these scores. This brief covers the companies, the technology, documented harms, the legal landscape, and actionable steps for viewers.

---

## 1. WHAT ARE THESE SCORES?

### A. Tenant Screening Scores

The tenant screening industry is estimated at **$1.85 billion in 2025**, projected to reach **$5.8 billion by 2033**. Roughly 2,000 companies offer screening software, and **9 in 10 landlords** use screening reports.

**SafeRent Solutions** (formerly CoreLogic SafeRent)
- **Product**: SafeRent Score / Registry ScorePLUS
- **Score Range**: 200-800
- **Data Used**: Credit history, non-tenancy debts, eviction history, rent-to-income ratio, "subprime records"
- **Key Issue**: Algorithm failed to account for housing vouchers that guarantee rent payment by a public agency
- **Settlement**: $2.275 million (November 2024) in *Louis v. SafeRent Solutions*

**TransUnion SmartMove (ResidentScore)**
- **Score Range**: 350-850
- **Data Used**: Payment history, credit utilization, credit history length, credit availability, inquiries
- **Marketing Claim**: "Predicts evictions 15% more often than a typical credit score" and "identifies 19% more skips"
- **Feature**: "Income Insights" checks whether credit behavior aligns with self-reported income

**RealPage**
- **Product**: AI Screening (launched 2019) -- "the first AI-based screening algorithm built specifically for the multifamily apartment rental industry"
- **Data Used**: Machine learning trained on **30+ million actual lease outcomes**, focusing on "willingness to pay"
- **Pricing Algorithm (YieldStar / AI Revenue Management)**: Contains lease transaction data from **13.5+ million rental units**; approximately **90% of property managers approve** the algorithm's suggested price changes; RealPage controls **80% of the commercial revenue management software market** with 31,700+ customers
- **Acquisition**: Thoma Bravo acquired RealPage for **$9.6 billion**
- **Legal Issues**: $3 million FTC settlement (2018) for inaccurate criminal record matching; DOJ antitrust action over rent-pricing algorithm (settlement November 2025 -- no fines, no admission of wrongdoing, but prohibited from using real-time confidential competitor data; nonpublic training data must be 12+ months old)
- **DOJ Parties**: Justice Department + AGs of North Carolina, California, Colorado, Connecticut, Minnesota, Oregon, Tennessee, and Washington

**AppFolio (FolioScreen)**
- **Product**: Automated tenant screening with customizable criteria
- **Credit Data**: Pulls from Experian -- provides credit score plus detailed history of accounts, payment patterns, and outstanding debts
- **How It Works**: Automated reports with customizable scoring criteria. Landlords set specific screening standards; system provides pass/fail recommendations
- **Scale**: AppFolio serves 9+ million rental units across the U.S.

**Yardi (ScreeningWorks Pro / RentGrow)**
- **Product**: Resident screening integrated into Yardi Voyager property management platform
- **Credit Data**: Equifax credit reports and Beacon credit scores, plus Experian RentBureau rental payment history and The Work Number for employment/income verification
- **How It Works**: Customizable scoring models tailored to market trends and property objectives. Criteria can accept, conditionally accept, or decline applicants. Includes fraud detection module
- **Key Feature**: Integrated Snappt document fraud detection to catch falsified pay stubs and bank statements
- **Scale**: Yardi serves 16+ million residential units worldwide

**LexisNexis RiskView (Alternative Credit Score)**
- **Product**: Alternative credit scoring for thin-file and no-file consumers
- **Score Range**: 501-900 (higher is better)
- **Data Used**: Evictions, liens, transience/address stability, assets, occupation, education, professional licenses, public records, credit-seeking behaviors from online and short-term lending markets
- **How It Works**: Creates a credit score for approximately 80% of the "unscorable" population -- people with thin or no traditional credit files. Uses alternative data and non-traditional information to evaluate risk
- **Industry Models**: Auto lending, short-term lending, retail credit cards, telecom/utility services -- each model weighted differently
- **Clients**: Available through FICO Marketplace; used by banks, credit unions, fintech lenders
- **Key Impact**: Scores people who thought they were "invisible" to the credit system. Consumers generally don't know this score exists and cannot access or dispute it in the same way as traditional credit scores

**Naborly / SingleKey**
- **Score Range**: 500-900 (color-coded green/yellow/red)
- **Data Used**: Social media analysis, phone record searches, criminal records, rental history, credit history, property-specific factors
- **Scale**: 500,000+ customers, 1.5 million rental units

**CoreLogic CrimSAFE**
- **Product**: Automated criminal background screening for tenant applications
- **Key Issue**: Denied housing based on dismissed charges (see Carmen Arroyo case below)

### B. Employment Screening Algorithms

The AI hiring solutions market is expected to exceed **$1.2 billion by 2033**. **82% of companies** now use AI to review resumes.

**HireVue**
- **Product**: AI-powered video interviewing and assessment
- **Scale**: 700+ customers including 1/3 of Fortune 100; 30-70 million video interviews processed
- **Pricing**: Starts at $35,000/year, typically exceeds $50,000
- **How It Works**: Analyzes content of spoken answers using deep learning. **Dropped facial analysis in January 2021** after audit showed it contributed "about 0.25% to a model's predictive power"
- **Clients**: Vodafone, Nike, Intel, Hilton, Carnival Cruise Lines
- **Regulatory Action**: EPIC filed FTC complaint (November 2019); ACLU/EEOC charges filed March 2025

**Pymetrics (now Harver)**
- **Product**: 12 neuroscience-based game assessments (25 minutes)
- **Founded by**: Neuroscientists from Harvard and MIT; acquired by Harver August 2022
- **How It Works**: Candidates play games measuring attention, decision-making, risk tolerance, emotional intelligence. Top performers establish a "success profile"; candidates scored on how closely they match
- **Clients**: BCG, Unilever

**Eightfold AI**
- **Score Range**: 1-5 scale for job applications
- **Data Used**: Claims to analyze "1 million job titles, 1 million skills, and profiles of 1 billion+ people"
- **Lawsuit**: January 2026 class action alleges Eightfold "scraped personal data on over one billion workers, scored job applicants on a zero-to-five scale, and discarded low-ranked candidates before a human being ever saw their applications"

**Workday**
- **Product**: AI-powered applicant recommendation and screening system (includes HiredScore AI features after acquisition)
- **Key Case**: *Mobley v. Workday* (N.D. Cal., 3:23-cv-00770). Derek Mobley, Black and over 40, sued after 100+ rejections. Received a rejection email at 1:30 AM on a weekend -- realized no human reviewed his application
- **May 2025**: Court granted conditional collective action certification under ADEA, potentially covering millions of applicants aged 40+ screened since September 2020
- **July 2025**: Judge expanded scope to include HiredScore AI features; ordered Workday to provide list of customers using HiredScore by August 20, 2025
- **Legal Significance**: Court held AI service providers can be directly liable for employment discrimination under an "agent" theory -- not just the employers who use the tool
- **Scale**: Workday serves 10,000+ customers including major employers across industries

**Kronos/UKG (Ultimate Kronos Group)**
- **Product**: Workforce management, personality/aptitude assessments, hiring screening tools
- **Key Historical Case**: *EEOC v. Kronos* -- The EEOC investigated Kronos's "Customer Service Assessment" personality test after a hearing- and speech-impaired applicant was rejected, alleging the test discriminated against people with disabilities
- **How It Works**: Kronos designed pre-employment personality tests used by major employers (Kroger, others) to screen hourly workers. Tests include clinical psychological screening questions
- **Connection to Kyle Behm Case**: Behm was rejected from a Kroger job in 2012 after failing a Kronos-designed personality test. He had bipolar disorder. Featured in HBO documentary *Persona*
- **Scale**: UKG serves 80,000+ customers in 150+ countries

### C. Insurance Risk Scores

**LexisNexis C.L.U.E. (Comprehensive Loss Underwriting Exchange)**
- Collects up to **7 years** of auto and home/property insurance claims
- Additional product: Telematics OnDemand (driving behavior data)
- Consumers can request their own CLUE report

**LexisNexis Risk Classifier**
- **Score Range**: 200-997 (high = better mortality risk)
- **Data Sources (basic)**: Motor vehicle records, public records, court records, property records, credit attributes, driving records
- **Data Sources (with medical data)**: All above PLUS prescription history, medical diagnoses, clinical lab reports
- **Key Finding**: "Relative risk mortality decreases by 39% if an individual owns one or more properties"
- **Clients**: Munich Re, SCOR (life insurers and reinsurers)

**Credit-Based Insurance Scores**
- LexisNexis: 200-997 | FICO Insurance Score: 250-900 | TransUnion: 300-850
- Used by: Geico, State Farm, USAA, Progressive, Allstate
- Progressive's own disclosure: "People who manage their money well tend to manage other important things in their lives well too"
- **Banned/restricted in**: California, Hawaii, Massachusetts, Maryland

**Verisk Analytics DrivingDNA Score**
- **Data**: 260 billion miles of driving behavior from 8+ million telematics-equipped vehicles (partnerships with Ford, GM, Honda, Hyundai)
- **Performance**: "12 times difference in expected losses between worst- and best-scoring groups"
- **Minimum Data**: Score calculated with as few as 10 weeks of driving data
- **Growth**: Vehicle telematics data expected to grow 137% over two years; shopping behavior data expected to grow 108%

**LexisNexis Attract Score (Credit-Based Insurance Score)**
- **Score Range**: 200-997
- **Good**: 776-997 | **Average**: 626-775 | **Below Average**: 501-625 | **Less Desirable**: 200-500
- **Data Sources**: Pulls from Experian, Equifax, and/or TransUnion credit bureaus -- factors include accounts in good standing, payment history, credit utilization, length of credit history
- **How It Works**: Predicts future insurance loss probability. Developed over 5 years using $19+ billion in policy premiums. Proprietary weighting of factors not disclosed
- **Variants**: Personal auto, homeowners, commercial insurance models
- **Market Penetration**: 95% of home insurers and 99%+ of auto insurers use some form of credit-based insurance score (CLUE/Attract or FICO Insurance Score)

**Verisk ClaimSearch & Claim Scoring**
- **Product**: ISO ClaimSearch (claims database) + ClaimDirector (fraud scoring)
- **ClaimDirector Score Range**: 0-999 (high score = more characteristics suggesting possible fraud)
- **Database**: 1.8 billion U.S.-based claims from 2,800+ contributors representing ~95% of the U.S. P&C insurance market
- **How It Works**: Uses machine learning and predictive models combining an individual insurer's real-time data with aggregated industry data. Provides fraud scores plus reason codes explaining why a claim was flagged. Includes digital media forensics, network analysis to reveal hidden entity relationships, and medical provider scoring
- **Consumer Impact**: A high ClaimDirector score can trigger Special Investigations Unit review, delaying or denying legitimate claims. Consumers have no visibility into their score

**FRISS (used by State Farm)**
- Assigns each policyholder a "risk score" based on neighborhood demographics, crime statistics, and social media data
- Subject of racial discrimination lawsuit (see Section 3)

### D. Alternative Data / Fintech Scores

**Upstart**
- **Revenue**: $1.04 billion FY 2025 (64% YoY increase)
- **Scale**: 500+ bank/credit union partners; 245,663 loans originated in Q4 2024 ($2.1 billion)
- **Data Variables**: 2,500+ data points trained on 50+ million repayment events (includes education, job history, bank transactions)
- **91% of loans fully automated** with no human intervention
- **Marketing Claim**: "Approve 44% more creditworthy borrowers than FICO models, cutting rates by 36%"

**Zest AI**
- **Funding**: $553.9 million raised (including $200M from Insight Partners)
- **Scale**: 600+ custom AI models deployed, 50+ patents; 180+ banks and credit unions from Freddie Mac to small local institutions
- **Clients**: Freddie Mac, Discover Financial, VyStar Credit Union
- **Data**: Uses ~300 variables (vs. traditional credit scores' 15-20) -- including utility payments, rental history, non-traditional financial behaviors
- **Performance**: 15% reduction in default rates, 30% increase in loan approvals
- **Equity Impact**: Loan approvals increased 49% for Latinos, 41% for Black applicants, 40% for women, 36% for elderly, 31% for AAPI applicants
- **Debiasing Method**: Uses "adversarial debiasing" -- two ML models compete: one predicts creditworthiness, the other tries to predict race/gender from the first model's output, driving both to improve until the predictor cannot distinguish protected class attributes
- **Named one of CNBC's 2025 World's Top FinTech Companies**

**Sift (formerly Sift Science)**
- **Product**: Digital Trust & Safety Platform / Sift Score
- **Score Range**: 0-100 (higher = greater fraud risk)
- **Scale**: 700+ customers; scores 1 trillion events per year using 16,000+ fraud signals accumulated over 13 years
- **How It Works**: Machine learning runs thousands of signals per interaction (time of day, email characteristics, login attempts, device fingerprinting, behavioral patterns). Scores user interactions on a specific site for a specific type of fraud, not individuals globally
- **Clients**: DoorDash, Airbnb, Yelp, Poshmark, OpenTable, Twitter/X, Zillow, Wayfair, SeatGeek
- **Valuation**: Over $1 billion (2021 funding round, $50M from Insight Partners)
- **Key Feature**: Sift Score API delivers real-time risk scores plus top 20 risk signals explaining why an action was flagged. Businesses set custom thresholds for auto-approve, step-up authentication, or manual review
- **Consumer Impact**: Consumers have no access to their Sift Score and no way to dispute or correct it. If scored as high-risk, users may be blocked from purchases, account creation, or returns with no explanation

**Skopos Labs**
- **Product**: AI-powered legislative and political risk prediction
- **Founded by**: Vanderbilt law professor J.B. Ruhl et al.
- **How It Works**: NLP and ML to predict whether bills pass Congress; generates daily exposure estimates for companies
- **Clients**: Thomson Reuters (powers Westlaw Edge Legislative Insights)

### E. Hidden Consumer Scores Most People Don't Know About

**ChexSystems (Fidelity National Information Services)**
- **Product**: Consumer banking history report and QualiFile Score
- **Score Range**: 100-899 (higher is better)
- **Thresholds**: 581+ generally means approval; 700+ clears path to open accounts; below 600 usually triggers denial
- **Data Used**: Bounced checks, overdrafts, account closures, unpaid bank fees, payday loan history, public records
- **How It Works**: Banks check ChexSystems before opening checking/savings accounts. A negative report can prevent someone from opening a bank account for up to 5 years
- **Scale**: Used by approximately 80% of U.S. banks and credit unions
- **Consumer Access**: Free annual report available at chexsystems.com
- **Key Issue**: Many consumers discover their ChexSystems record only after being denied a bank account, creating a cycle where people without bank accounts rely on expensive check-cashing services

**NCTUE (National Consumer Telecom & Utilities Exchange)**
- **Product**: Telecom and utilities payment history database
- **Managed by**: Equifax (contracted servicer)
- **Data Used**: Payment histories, delinquencies, charge-offs, and connect requests for telecommunications, pay TV, home security, and utility (electric, gas, water) services
- **How It Works**: When you apply for a new phone plan, cable service, or utility account, the provider checks NCTUE. Poor history can result in higher deposits or denial of service
- **Scale**: Called "the largest consumer reporting bureau no one has heard of" by consumer advocates
- **Consumer Access**: Free annual report at nctue.com
- **Key Issue**: Most consumers have no idea this database exists until they're asked for a large security deposit

**The Retail Equation (now Appriss Retail)**
- **Product**: Return Activity Report / Return Authorization Score
- **Score Range**: Proprietary (no public score range disclosed)
- **Data Used**: Return frequency, item value, return-to-purchase ratio, time of return, whether items are commonly stolen, return patterns
- **How It Works**: Integrated into point-of-sale systems at major retailers. Analyzes every return in real time. Most customers have a purchase-to-return rate of 5-15%; exceeding that triggers warnings, then outright return bans
- **Retailers Using It**: Best Buy, Home Depot, J.C. Penney, Sephora, Victoria's Secret
- **Scale**: Designed to identify the 1% of shoppers whose behaviors mimic return fraud or abuse
- **Consumer Impact**: Consumers can be permanently banned from making returns at specific retailers with no warning and no appeal process visible at the store level. Can request a Return Activity Report by emailing returnactivityreport@theretailequation.com
- **Key Issue**: Legitimate returns (defective products, wrong sizes, gifts) can trigger flags if frequency is high enough

**FICO Medication Adherence Score**
- **Product**: Predictive score for pharmaceutical companies and health insurers
- **Score Range**: Not publicly disclosed
- **Data Used**: Publicly available third-party data sources -- critically, NO prescription claims or sensitive health information required. Uses demographic, socioeconomic, and behavioral proxies
- **How It Works**: Predicts an individual patient's propensity toward medication adherence over the next 12 months. Because it requires minimal patient information, it can be generated for any patient population
- **Purpose**: Pharmaceutical companies use it to target "non-adherent" patients with outreach; insurers use it for care/utilization management
- **Key Concern**: Scores patients on whether they'll take their medicine based on non-medical proxies -- essentially a behavioral prediction score applied to healthcare without patients' knowledge

**LexisNexis ThreatMetrix**
- **Product**: Digital identity intelligence and device fingerprinting
- **Score Range**: Proprietary risk scores per transaction
- **Data Used**: Device fingerprinting (hardware, software, browser config), geographic location, network properties, user behavior data, online ID attributes (hashed by client), IP intelligence
- **How It Works**: When you interact with any website or app using ThreatMetrix, it creates a digital identity profile from your device characteristics and behavioral patterns, producing risk scores in real time. Uses machine learning and behavioral analytics
- **Scale**: Processes billions of transactions annually for financial institutions, e-commerce, and government agencies
- **Consumer Impact**: Operates invisibly -- consumers don't know they're being scored. A high risk score can result in blocked transactions, step-up authentication requirements, or account lockouts with no explanation referencing ThreatMetrix

**Zeta Global Consumer Scores**
- **Product**: Customer value ratings and behavioral scores
- **Database**: 700+ million people with an average of 2,500+ data points per person
- **How It Works**: Rates customer value to help companies decide what type of service to provide -- including how quickly to address requests and problems
- **Consumer Impact**: Higher-value customers may receive faster customer service, better offers, and more responsive support. Lower-value customers may experience longer wait times and fewer accommodations

### F. Social Media Scoring

**Lenddo (now LenddoEFL)**
- **Score Range**: 0-1,000
- **Markets**: Mexico, Philippines, Colombia, other emerging markets
- **Data**: 120+ social media profiles (Facebook, LinkedIn, Twitter, Gmail, Yahoo), plus smartphone data (messaging history, browser history, installed apps, WiFi networks, battery levels)
- **Mechanism**: Borrowers select a "Trusted Network" of 3+ people. If the borrower defaults, their network connections' Lenddo scores also suffer
- **Privacy International** called social media credit scoring "fintech's dirty little secret"

**Broader Landscape**
- Data brokers collect and sell social media information for housing, job, and lending decisions
- Some lenders "scrape information from public records or social media accounts to build a credit profile without borrowers' knowledge"
- Greenlining Institute: "Borrowers don't know what information is used for calculating alternative credit scores, so they can't contest erroneous information"

---

## 2. HOW DO THEY WORK?

### Data Inputs
- **Traditional**: Credit reports, eviction records, criminal records, employment history
- **Alternative**: Shopping habits, social media activity, location data, neighborhood demographics, app usage, browser history, utility payments, rental payments, gig economy income
- **Behavioral**: Driving behavior (telematics), online activity patterns, typing patterns, game-playing behavior (Pymetrics)
- **Biometric**: Voice analysis, facial expressions (HireVue, pre-2021), typing cadence
- **Environmental**: Property records, neighborhood crime statistics, school district data, proximity to environmental hazards

### Decision Speed
- Upstart: **91% of loans fully automated** -- no human touches them
- Eightfold AI: Scores candidates 1-5 and "discards low-ranked candidates before a human being ever saw their applications"
- Derek Mobley received a rejection email at **1:30 AM on a weekend** -- clearly algorithmic
- RealPage: Instant approve/deny recommendations based on 30M+ training outcomes
- Cigna: One doctor denied **60,000 claims in a single month** using AI without opening patient files

### Machine Learning Bias Issues

**Racial Proxies**
- Neighborhood demographics, ZIP codes, school names, and property values serve as proxies for race
- SafeRent's algorithm disproportionately gave lower scores to Black and Hispanic applicants
- Brookings study: White-associated names preferred in **85.1%** of AI resume screening tests; Black-associated names in just 8.6%
- Healthcare algorithm scored Black patients lower than white patients with identical chronic conditions

**Economic Proxies**
- Credit scores: Black median 612, Hispanic 661, White 725 (Urban Institute, 2022)
- Housing voucher holders systematically penalized despite guaranteed rent payments
- Property ownership used as mortality predictor (LexisNexis: 39% lower risk for property owners)

**Geographic Proxies**
- State Farm's FRISS uses neighborhood demographics and crime statistics
- California Insurance Commissioner flagged that geographic data has "strong potential to disguise bias and discrimination"

---

## 3. DOCUMENTED HARMS -- NAMED VICTIMS & SPECIFIC CASES

### A. Housing Denials -- Tenant Screening Scores

**Mary Louis** (Malden, Massachusetts, 2021)
- **Who**: Black woman, housing voucher holder, 16 years of on-time rent payments
- **What happened**: Applied to Granada Highlands apartments. Her housing voucher covered approximately 69% of her rent. Despite a spotless 16-year tenancy record, SafeRent's algorithm gave her a low score that ignored the value of her voucher and penalized her for credit history including non-tenancy debts
- **Company**: SafeRent Solutions (formerly CoreLogic Rental Property Solutions)
- **Outcome**: Lead plaintiff in *Louis et al. v. SafeRent Solutions* (1:22-cv-10800, D. Mass.). U.S. DOJ filed a Statement of Interest supporting plaintiffs (January 2023). $2.275 million settlement approved November 2024. SafeRent now barred from issuing SafeRent Scores for voucher holders; any future scoring tool must be validated by an independent third-party agreed to by plaintiffs
- **Sources**: [Cohen Milstein case page](https://www.cohenmilstein.com/case-study/louis-et-al-v-saferent-solutions-et-al/), [NCLC](https://www.nclc.org/saferent-solution-accused-of-illegally-discriminating-against-black-and-hispanic-rental-applicants/), [DOJ Statement of Interest](https://www.justice.gov/d9/2023-01/u.s._statement_of_interest_-_louis_et_al_v._saferent_et_al.pdf)

**Monica Douglas** (Massachusetts, 2022)
- **Who**: Black woman, housing voucher holder, co-plaintiff with Mary Louis
- **What happened**: Also denied housing after SafeRent's algorithm assigned her a low score that failed to account for her housing voucher subsidy. The algorithm treated voucher holders identically to unsubsidized tenants, systematically disadvantaging them
- **Company**: SafeRent Solutions
- **Outcome**: Co-plaintiff in *Louis v. SafeRent*; covered by the $2.275M class settlement
- **Sources**: [CommonWealth Beacon](https://commonwealthbeacon.org/courts/lawsuit-alleges-racial-discrimination-in-tenant-screening-tool/), [NCLC](https://www.nclc.org/resources/louis-v-saferent-solutions-llc/)

**Carmen Arroyo & Mikhail Arroyo** (Connecticut)
- **Who**: Carmen Arroyo, mother and conservator of her son Mikhail, who was severely injured in a July 2015 accident that left him unable to speak, walk, or care for himself
- **What happened**: Carmen asked her landlord for permission to move Mikhail into her home so she could care for him. The landlord ran a background check through CoreLogic's CrimSAFE automated screening system, which returned a bare notation that Mikhail had a "disqualifying [criminal] record." The underlying record was a 2014 retail theft charge in Pennsylvania for $150 -- a charge that had been **dropped and never resulted in a conviction**. CoreLogic refused to provide the Arroyos a copy of Mikhail's actual criminal history. **Mikhail was left in an institution for approximately one year** while his mother fought the denial
- **Company**: CoreLogic Rental Property Solutions (CrimSAFE product)
- **Outcome**: Lead case in *Connecticut Fair Housing Center et al. v. CoreLogic Rental Property Solutions* (3:2018cv00705, D. Conn., filed 2018). District court ruled CoreLogic not subject to FHA after bench trial. Second Circuit heard oral arguments November 2024; appeal pending
- **Sources**: [NHLP case page](https://www.nhlp.org/our-initiatives/arroyo-v-corelogic/), [CT Mirror](https://ctmirror.org/2019/03/28/a-tenant-blacklist-compiled-by-algorithm/), [The Markup](https://themarkup.org/locked-out/2020/09/24/fair-housing-laws-algorithms-tenant-screenings), [NBC News](https://www.nbcnews.com/tech/tech-news/tenant-screening-software-faces-national-reckoning-n1260975)

**Marco Antonio Fernandez** (Fort Meade, Maryland area, 2018)
- **Who**: Active-duty Navy serviceman with **top-secret security clearance**, returning from a yearlong deployment in South Korea
- **What happened**: Searched for an apartment near Fort Meade, Maryland. Tenant screening software rejected him because it found he had a **drug conviction and three misdemeanors for petty theft**. The algorithm had confused him with **Marco Alberto Fernandez Santana, an alleged Mexican drug trafficker**. A U.S. military intelligence professional with top-secret clearance was denied housing because a screening algorithm matched him to a cartel suspect
- **Company**: RentGrow (subsidiary of Yardi Systems) and CoreLogic Credco
- **Outcome**: Filed proposed class-action in Baltimore (April 2019) against RentGrow; also sued CoreLogic Credco in federal court in San Diego
- **Sources**: [NBC News](https://www.nbcnews.com/tech/tech-news/tenant-screening-software-faces-national-reckoning-n1260975), [The Markup](https://themarkup.org/locked-out/2020/05/28/access-denied-faulty-automated-background-checks-freeze-out-renters)

**Kim Fuller** (Baltimore, Maryland, 2021)
- **Who**: Mental health services coordinator for the state of Maryland. Her 83-year-old mother was struggling to get around their narrow three-story row house
- **What happened**: Applied to an apartment complex 3 miles away billed as "luxury living" for people 55+. Her salary met income requirements; she had never been evicted; credit score was 632 (fair) after a health crisis forced bankruptcy eight years earlier. Application denied with no reason given. She raised her credit score to 663 and applied to another complex owned by the same company (Habitat America) -- denied again. A form from RentGrow highlighted "credit history" as the reason but provided no further explanation. **Fuller worried the denial was a form of illegal redlining**. She filed complaints with the CFPB against both RentGrow and Habitat America -- the CFPB rejected both complaints, saying it was "unable to send the complaints to the company"
- **Company**: RentGrow (subsidiary of Yardi Systems), used by Habitat America
- **Outcome**: Complaints rejected by CFPB. Story became a centerpiece of ProPublica's "shadow credit score" investigation
- **Sources**: [ProPublica, "How Your Shadow Credit Score Could Decide Whether You Get an Apartment" (March 2022)](https://www.propublica.org/article/how-your-shadow-credit-score-could-decide-whether-you-get-an-apartment)

**Chloe Crawford** (college student, 2018)
- **Who**: College student arriving at a new building near campus
- **What happened**: Her new landlord demanded an extra month's rent as a deposit because of her low tenant screening score, totaling more than $1,000. Her tenant score was 685 out of 1,000 from LeasingDesk (a SafeRent/CoreLogic product), which flagged her credit history and rent-to-income ratio as "unsatisfactory"
- **Company**: LeasingDesk (SafeRent/CoreLogic)
- **Outcome**: Forced to pay the additional deposit
- **Sources**: [ProPublica](https://www.propublica.org/article/how-your-shadow-credit-score-could-decide-whether-you-get-an-apartment)

**Glenn Patrick Thompson Sr. & Glenn Patrick Thompson Jr.** (near Seattle, Washington)
- **Who**: Father and son
- **What happened**: Left homeless after tenant screening company On-Site (now RealPage) told two different landlords that both father and son had been previously evicted. The eviction record actually belonged to a **Patricia Thompson** -- not related to them. The screening company's matching algorithm connected them to someone else's record solely based on a shared last name
- **Company**: On-Site (now part of RealPage)
- **Outcome**: Left homeless; case cited in The Markup investigation
- **Sources**: [The Markup, "Access Denied" (May 2020)](https://themarkup.org/locked-out/2020/05/28/access-denied-faulty-automated-background-checks-freeze-out-renters)

**William Hall Jr.** (Georgia)
- **Who**: Prospective tenant in Georgia
- **What happened**: Lost out on renting a duplex after TransUnion Rental Screening Solutions reported that he had **sexually abused a minor**. The criminal record belonged to a different William Hall who was **30 years older** and possibly dead
- **Company**: TransUnion Rental Screening Solutions
- **Outcome**: Denied housing based on false sex crime allegation
- **Sources**: [The Markup](https://themarkup.org/locked-out/2020/05/28/access-denied-faulty-automated-background-checks-freeze-out-renters)

**Samantha Johnson** (St. Helens, Oregon, 2018)
- **Who**: Prospective tenant in Oregon
- **What happened**: Background check came back showing she was a criminal -- **none of the charges were hers**. The automated check cast a wide net, pulling in records from states where she had never lived, matching her to records from four other Samantha Johnsons and one woman who had used the name as an alias. One record said she was an **"active inmate" in a Kentucky jail** at the time of application. The women's middle names, races, and dates of birth didn't match her own
- **Company**: Automated tenant screening company (name not specified in reporting)
- **Outcome**: Eventually convinced the landlord she wasn't a criminal and got the apartment; ongoing problems with screening errors
- **Sources**: [The Markup](https://themarkup.org/locked-out/2020/05/28/access-denied-faulty-automated-background-checks-freeze-out-renters)

**Systemic: RealPage False Criminal Records** (2012-2017)
- System matched criminal records using only last name + non-exact first name/DOB. One background check company produced **11,000 inaccurate renter background reports between 2014 and 2019**. $3 million FTC settlement (2018)

**Systemic: AppFolio Inaccurate Reports** (pre-2019)
- AppFolio failed to ensure criminal and eviction records from third-party vendors were accurate. Reports included records for wrong individuals, with missing dispositions, and duplicate entries. Despite numerous consumer complaints, AppFolio did not fix its procedures. **$4.25 million FTC settlement (December 2020)**
- **Sources**: [FTC press release](https://www.ftc.gov/news-events/news/press-releases/2020/12/tenant-background-report-provider-settles-ftc-allegations-it-failed-follow-accuracy-requirements)

**Systemic: TransUnion Fabricated Evictions**
- Double-counted eviction events, making it appear consumers had multiple evictions when only one existed. Labeled disputed amounts as "Judgment Amount" suggesting a court ruling. Included sealed and expunged records. $15 million settlement (FTC/CFPB, 2023)

**Systemic: CFPB Complaint Data** (2019-2022)
- Renters submitted approximately **26,700 complaints** related to tenant screening from January 2019 through September 2022, increasing year-over-year
- **Sources**: [CFPB Consumer Snapshot (November 2022)](https://www.consumerfinance.gov/about-us/newsroom/cfpb-reports-highlight-problems-with-tenant-background-checks/)

### B. Job Denials -- AI Hiring Algorithms

**Derek Mobley** (Northern California, 2023)
- **Who**: African American man over age 40 who self-identifies as having anxiety and depression
- **What happened**: Applied for **more than 100 jobs** using Workday's platform over seven years and was not hired for a single position. In one documented instance, he submitted a job application at **12:55 a.m. and received a rejection notice less than an hour later at 1:50 a.m.** -- demonstrating no human reviewed his application. Four additional plaintiffs joined, all over age 40, all claiming hundreds of applications through Workday with universal rejection
- **Company**: Workday, Inc.
- **Outcome**: Filed February 2023 in N.D. California. May 2025: Judge Rita Lin granted preliminary collective action certification under ADEA for all applicants ages 40+ denied through Workday's platform since September 2020
- **Sources**: [CNN](https://www.cnn.com/2025/05/22/tech/workday-ai-hiring-discrimination-lawsuit), [FairNow](https://fairnow.ai/workday-lawsuit-resume-screening/), [Columbia Black Pre-Law Society](https://blackprelaw.studentgroups.columbia.edu/news/mobley-v-workday-and-ai-discrimination)

**"D.K."** (Colorado, 2024) -- name redacted in filings
- **Who**: Indigenous and Deaf woman, pursuing a master's in data science. Communicates using ASL and speaks English with a deaf accent. Employed by Intuit with high performance scores
- **What happened**: In spring 2024, encouraged by her supervisor to apply for a seasonal manager position at Intuit. Required to use HireVue's video interview platform with automated speech recognition. Research cited in the complaint shows ASR systems perform "**ten times worse**" for deaf individuals, with approximately every other word transcribed incorrectly. D.K. requested human-generated captioning -- **Intuit denied the request**. Some audible portions of HireVue's platform lacked subtitles entirely. After the interview, she was rejected. Feedback told her to work on "effective communication," provide "concise and direct answers," and "practice active listening" -- all coded references to her disability
- **Company**: HireVue and Intuit
- **Outcome**: ACLU filed complaints with Colorado Civil Rights Division and EEOC (March 19, 2025). Alleges violations of CADA, ADA, and Title VII
- **Sources**: [ACLU complaint (PDF)](https://assets.aclu.org/live/uploads/2025/03/Redacted-HireVue_Intuit-Complaint-of-Discrimination_Redacted.pdf), [Public Justice](https://www.publicjustice.net/hirevue-intuit-artificial-intelligence-biased-hiring/), [HR Dive](https://www.hrdive.com/news/ai-intuit-hirevue-deaf-indigenous-employee-discrimination-aclu/743273/)

**iTutorGroup -- 200+ Older Workers Rejected** (EEOC, 2022-2023)
- **Who**: More than 200 qualified U.S.-based applicants for English-language tutoring positions
- **What happened**: iTutorGroup programmed its software to **automatically reject female applicants aged 55+ and male applicants aged 60+**. Discovered when an applicant submitted two identical applications differing only in birth date -- **only received an interview when using the fake, younger birth date**
- **Company**: iTutorGroup, Inc.
- **Outcome**: First-ever EEOC AI discrimination settlement (August 2023). $365,000 distributed to rejected applicants
- **Sources**: [EEOC press release](https://www.eeoc.gov/newsroom/itutorgroup-pay-365000-settle-eeoc-discriminatory-hiring-suit), [Sullivan & Cromwell](https://www.sullcrom.com/insights/blogs/2023/August/EEOC-Settles-First-AI-Discrimination-Lawsuit)

**Amazon Resume AI** (2014-2017, internal)
- **What happened**: Amazon developed an AI system to rate candidates 1-5 stars. Trained on 10 years of male-dominated resumes, it penalized resumes containing "women's" (e.g., "women's chess club captain") and names of all-women's colleges. Favored "macho verbs" like "executed" and "captured." **Team disbanded** by early 2017
- **Company**: Amazon (internal tool, never deployed externally)
- **Outcome**: Scrapped. Became a landmark cautionary case for AI hiring bias
- **Sources**: [Reuters/MIT Tech Review (October 2018)](https://www.technologyreview.com/2018/10/10/139858/amazon-ditched-ai-recruitment-software-because-it-was-biased-against-women/), [ACLU](https://www.aclu.org/news/womens-rights/why-amazons-automated-hiring-tool-discriminated-against)

**Kyle Behm** (Georgia, 2012-2019)
- **Who**: Young man with bipolar disorder
- **What happened**: Applied for a Kroger job in 2012, rejected after a personality test using clinical psychological screening questions. Systematically filtered out due to his mental health condition. **Kyle died by suicide in 2019.** His father Roland Behm became an advocate against personality testing in hiring
- **Company**: Kroger, using personality assessment tools
- **Outcome**: Story featured in the 2021 HBO documentary *Persona: The Dark Truth Behind Personality Tests*

### C. Insurance Denials & Discriminatory Scoring

**Huskey & Wynn v. State Farm** (N.D. Ill., December 14, 2022)
- **Who**: Black first-time claimants in Illinois
- **What happened**: After storm damage, claims flagged by State Farm's AI fraud-detection algorithm (FRISS). Huskey experienced **two months of delay** while water damage spread through her kitchen and bathrooms. FRISS uses neighborhood demographics, crime statistics, and social media data
- **Company**: State Farm (using FRISS AI fraud-detection)
- **Outcome**: Class action ongoing

**Frances Walter** (Medicare Advantage)
- **Who**: Medicare Advantage enrollee, allergic to opioids and common pain relievers
- **What happened**: NaviHealth's algorithm predicted recovery in **16.6 days** and insurer cut off payment despite medical notes showing she couldn't dress herself, use the bathroom, or operate a walker
- **Company**: NaviHealth (UnitedHealth Group subsidiary)
- **Sources**: STAT News

**Jose C. DeHoyos et al. v. Allstate Corporation** (W.D. Texas, filed November 2001)
- **Who**: Jose C. DeHoyos and other minority policyholders in Texas
- **What happened**: Alleged Allstate raised auto insurance premiums or assigned minority customers to higher-cost subsidiaries based on race through credit-based insurance scoring and geographical factors serving as racial proxies
- **Company**: Allstate Insurance Company
- **Outcome**: U.S. Supreme Court declined Allstate's appeal (2004). Settlement: Allstate rolled out new scoring algorithm; minority customers could seek $50-$150 refunds. Named plaintiffs received $5,000 each
- **Sources**: [Insurance Journal (2004)](https://www.insurancejournal.com/news/national/2004/04/28/41541.htm), [Insurance Journal (2006)](https://www.insurancejournal.com/news/southcentral/2006/06/02/69105.htm)

**Systemic: Auto Insurance Racial Pricing Disparities** (ProPublica & Consumer Federation of America)
- Consumer Federation of America (2015): predominantly African-American neighborhoods pay **70% more on average** for auto insurance premiums. Allstate, Geico, Liberty Mutual charged premiums **30% higher on average** in minority-majority zip codes vs. whiter neighborhoods with similar accident costs. Safe driver in Buffalo's predominantly African American 14215 ZIP quoted **34% higher premiums** than identical driver in neighboring majority-white 14226 ZIP
- **Sources**: [ProPublica](https://www.propublica.org/article/minority-neighborhoods-higher-car-insurance-premiums-white-areas-same-risk), [Consumer Federation of America](https://consumerfed.org/press_release/systemic-racism-in-auto-insurance-exists-and-must-be-addressed-by-insurance-commissioners-and-lawmakers/)

**Systemic: LexisNexis C.L.U.E. Database Errors**
- Class action (*Contreras v. LexisNexis Risk Solutions, Inc.*) alleged LexisNexis failed to verify accuracy; because reports are distributed across the insurance industry, a **single error can ripple through multiple companies**
- **Sources**: [Consumer Attorneys analysis](https://consumerattorneys.com/article/the-hidden-power-of-lexisnexis-and-the-lives-it-quietly-derails)

**Cigna Bulk Denials** (systemic)
- One Cigna doctor denied **60,000 claims in a single month** using AI algorithms without opening patient files. Nationally, insurers denied **49+ million claims in 2021**; patients appealed **less than 0.2%**

### D. Healthcare Algorithm Racial Bias

**Optum/UnitedHealth Health Algorithm** (exposed October 2019)
- **Study**: **Ziad Obermeyer (UC Berkeley), Brian Powers, Christine Vogeli, and Sendhil Mullainathan**, published in *Science* 366:447-453 (October 25, 2019)
- **What**: A widely used Optum algorithm managed the health of approximately **200 million patients** across the U.S. It exhibited significant racial bias because it predicted health care **costs** rather than **illness**. Because Black patients historically received less care, they spent less -- so the algorithm concluded they were healthier
- **Key numbers**: Among patients at the 97th percentile risk score, Black patients had **26% more chronic illnesses** than white patients. Across 3.7 million patients, Black patients had **almost 50,000 more chronic conditions** than equally-scored white patients. Fixing the bias would increase Black patients receiving additional care from **17.7% to 46.5%**
- **Outcome**: Optum developed a revised algorithm achieving an **84% reduction in bias**. New York state regulators launched a probe
- **Sources**: [Obermeyer et al., *Science* (2019)](https://www.science.org/doi/10.1126/science.aax2342), [Washington Post](https://www.washingtonpost.com/health/2019/10/24/racial-bias-medical-algorithm-favors-white-patients-over-sicker-black-patients/), [NBC News](https://www.nbcnews.com/news/nbcblk/racial-bias-found-widely-used-health-care-algorithm-n1076436)

---

## 4. LAWSUITS & INVESTIGATIONS

### Major Cases

| Case | Court | Filed | Status | Amount |
|------|-------|-------|--------|--------|
| **Louis v. SafeRent Solutions** (1:22-cv-10800) | D. Mass. | May 2022 | Settled Nov 2024 | **$2.275M** |
| **CT Fair Housing Center v. CoreLogic** (3:2018cv00705) | D. Conn. | 2018 | Appeal pending, 2nd Circuit | Pending |
| **EEOC v. iTutorGroup** (1:22-cv-02565) | E.D.N.Y. | 2022 | Consent decree Sept 2023 | **$365K** |
| **Mobley v. Workday** (3:23-cv-00770) | N.D. Cal. | 2023 | Collective certified May 2025 | Pending |
| **United States v. Meta Platforms** | S.D.N.Y. | June 2022 | Settled June 2022 | **$115,054** |
| **DOJ v. RealPage** (antitrust) | Federal | Aug 2024 | Settlement pending | Injunctive |
| **FTC/CFPB v. TransUnion & TURSS** | Federal | Oct 2023 | Settled | **$15M** |
| **FTC v. RealPage** (FCRA) | Federal | Oct 2018 | Settled | **$3M** |
| **Huskey v. State Farm** | N.D. Ill. | Dec 2022 | Ongoing | Class action |
| **Eightfold AI class action** | Federal | Jan 2026 | Filed | Pending |
| **Deyerler v. HireVue** (BIPA) | Illinois | Jan 2022 | MTD largely denied Feb 2024 | Pending |
| **ACLU v. Intuit/HireVue** | EEOC/Colorado | March 2025 | Filed | Pending |

### FTC Reports & Investigations
- **"Data Brokers: A Call for Transparency and Accountability"** (May 2014)
- **"Big Data: A Tool for Inclusion or Exclusion?"** (January 2016)
- **FTC Operation AI Comply** enforcement sweep (September 2024)
- **EPIC FTC Complaint re: HireVue** (November 6, 2019)

### CFPB Reports (November 2022)
- "Consumer Snapshot: Tenant Background Checks"
- "Tenant Background Checks Market"
- Key finding: Many screening companies use "wildcard" matching leading to erroneous criminal/eviction record matches

### HUD Guidance (May 2, 2024)
Two guidance documents clarifying that housing providers, screening companies, and ad platforms can all be liable under the Fair Housing Act for algorithmic discrimination.

### Academic Studies

**Brookings Institution -- AI Resume Screening Bias**
White-associated names preferred in **85.1%** of tests; Black-associated names in **8.6%**. Equal selection in only 6.3% of tests.

**Urban Institute -- Credit Score Racial Disparities (2022)**
Black consumers: median score 612 | Hispanic: 661 | White: 725

**NCLC "Digital Denials" (September 2023)**
Found **no empirical or scientific evidence** that credit reports/scores accurately predict successful tenancy. "Credit scores are designed for one thing only -- to predict whether a consumer will be late on a loan."

**University of Chicago -- Pretrial Release Algorithm**
Recommends 8 percentage point higher release rate for white defendants than equally qualified Black defendants, explaining 77% of the observed racial disparity.

**University Dropout Prediction Model**
Used by 500+ universities. Black students up to **4x as likely** as similar white peers to be flagged "high risk."

**Rosen, Garboden & Cossyleon** (American Sociological Review, 2021)
Interviewed 157 landlords documenting how algorithms serve as mechanisms for racial discrimination with plausible deniability. Published in *American Sociological Review* 86(5). Found that large-portfolio landlords rely on screening algorithms while small landlords use informal "gut feelings" and home visits -- both pathways enabling discrimination.

**Obermeyer, Powers, Vogeli & Mullainathan** (*Science* 366:447-453, October 2019)
Landmark study showing a widely used health algorithm (Optum) exhibited racial bias affecting ~200 million patients. Black patients at the 97th percentile risk score had 26% more chronic illnesses than white patients at the same score. Fixing the algorithm would increase Black patients receiving additional care from 17.7% to 46.5%. Algorithm predicted costs instead of illness, and because Black patients received less care historically, the system concluded they were healthier.

**FTC -- Credit-Based Insurance Scoring** (2007)
Found that African Americans and Hispanics are strongly overrepresented in the lowest insurance credit scoring categories. Led to ongoing debate about whether credit-based insurance scores constitute disparate impact discrimination.

**National Bureau of Economic Research -- Rental Discrimination** (2021)
Landlords responded to white renters' applications **60% of the time**, while responses to Black and Latino renters' applications were **5.6 and 2.8 percentage points lower**, respectively.

**So (MIT)** (Housing Policy Debate, ~2023)
Examined how landlords assess tenant screening reports. Found landlords relied primarily on the **scores returned rather than the underlying data** -- even when underlying data contained critical context such as dismissed charges or resolved evictions.

**New York Criminal Record Study**
87% of criminal records contained at least one error. 69% of arrest records missing outcome data.

**FTC 2007 -- Credit Score Racial Disparities in Insurance**
Found African Americans and Hispanics strongly overrepresented in the lowest credit scoring categories used by auto insurers. VantageScore data (2021): Black consumers median 639, White consumers median 730 -- nearly 100-point gap.

---

## 5. THE LEGAL LANDSCAPE

### A. Fair Credit Reporting Act (FCRA) -- Written 1970, Pre-Algorithm

**What it covers**: Consumer reporting agencies must ensure accuracy, provide adverse action notices, allow consumer file access, and limit report access to permissible purposes.

**Critical gaps for algorithmic scores**:
- Alternative data (social media, app usage, behavioral data) falls outside traditional FCRA definitions
- Data brokers involved in lending never subject to FCRA oversight until proposed 2024 CFPB rulemaking (unlikely to survive current administration)
- Companies argue they aren't "consumer reporting agencies," sidestepping all requirements
- Trade secret protection shields algorithmic logic from disclosure
- Dispute mechanism designed for traditional data -- unclear whether correcting data changes a predictive score
- When only summarized information (e.g., a tenant screening score) is provided to landlords, the CFPB interprets FCRA to require disclosure of the underlying information -- but enforcement is minimal
- Tenant screening algorithms "collapse any context or nuance in tenants' backgrounds, encouraging landlords to apply rigid rules that deny tenants individualized assessment" (CDT)
- Prior rental payment history is "overwhelmingly not reflected" in algorithmic risk scores (CFPB), meaning good tenants get no credit for years of on-time payments

**Key CFPB Guidance**:
- **Circular 2022-03** (May 26, 2022): Adverse action notification requirements apply to credit decisions based on complex algorithms. "A creditor's lack of understanding of its own methods is not a cognizable defense." Must provide specific, principal reasons even when using AI/ML models -- cannot use vague reasons like "our model flagged your application"
- **Circular 2023-03** (September 19, 2023): Creditors using AI underwriting may NOT rely on CFPB model adverse action notice forms if specific denial reasons are not captured by standard forms. Must create custom reason codes reflecting actual AI-driven factors
- **Circular 2024-06**: Warned employers that third-party AI algorithmic scores for hiring must comply with FCRA
- **May 2025**: CFPB withdrew dozens of interpretive rules and circulars, creating enforcement uncertainty

**CFPB Status -- Critical Context (March 2026)**:
- In February 2025, Acting Director Russell Vought shuttered the CFPB, halted funding, fired ~1,500 of 1,700 employees
- Agency dropped lawsuits against Bank of America, JPMorgan Chase, Wells Fargo, and Capital One
- December 30, 2025: Federal judge ruled CFPB must remain funded
- As of March 2026, CFPB remains open but with drastically reduced capacity -- algorithmic oversight effectively on hold
- No new enforcement actions being pursued against algorithmic scoring practices

### B. FTC Authority Over Scoring Practices

**Legal Basis**: Section 5 of the FTC Act prohibits "unfair and deceptive acts and practices"
- "Deceptive": representation, omission, or practice that is material and likely to mislead a reasonable consumer
- "Unfair": causes or will likely cause substantial injury consumers cannot reasonably avoid, not outweighed by countervailing benefits

**Key Enforcement Actions**:
- **Rite Aid (December 2023)**: First FTC action addressing algorithmic discrimination. AI facial recognition in hundreds of stores (2012-2020). Black, Asian, Latinx, and women consumers at higher false positive risk. Settlement: **5-year ban on facial recognition** + required deletion of all images AND all algorithms/models built from those images
- **RealPage (2018)**: $3 million settlement for inaccurate criminal record matching
- **Operation AI Comply (September 2024)**: Enforcement sweep targeting AI-powered deceptive/unfair practices

**Joint Agency Statement on AI Discrimination (April 2023)**:
- FTC, CFPB, EEOC, and DOJ Civil Rights Division joint statement warning existing laws apply to algorithmic discrimination

**FTC Limitations**:
- No standalone federal AI discrimination law
- Cannot impose civil fines for first-time Section 5 violations (only injunctive relief)
- Algorithm deletion remedy powerful but rarely used
- Current FTC leadership has deprioritized algorithmic discrimination enforcement

### C. EEOC on Algorithmic Hiring

**Title VII Technical Assistance** (May 18, 2023):
- Disparate impact analysis applies to AI hiring tools
- Employers cannot outsource liability to vendors -- they remain liable even if vendor assures no bias
- Traditional four-fifths (80%) rule applies to selection rates
- Employers must prove "job-related and consistent with business necessity" to defend disparate impact

**ADA Guidance** (May 2022): Addressed how algorithmic tools may discriminate against individuals with disabilities.

**First enforcement action**: iTutorGroup, $365,000 settlement (2023)

### D. State Laws -- Tenant Screening

**Washington -- Fair Tenant Screening Act (SHB 1257)**
- Requires portable "Comprehensive Reusable Tenant Screening Reports" valid **30 days**
- Must include: credit report, criminal records from every state (7 years) + sex offender registries, eviction history (7 years)
- Landlords accepting portable reports cannot charge for separate screening
- Info: https://www.washingtonlawhelp.org/en/tenant-screening-your-rights

**Colorado -- HB 23-1099 / HB 24-1098**
- HB 23-1099: Portable Tenant Screening Reports
- HB 24-1098 (April 2024): Just cause eviction protections

**Minnesota -- SF 2087 (effective August 1, 2025)**
- Bans tenant screening software using **nonpublic competitor data** to set rent (targets RealPage)
- Bans screening algorithms with **disproportionate effect on protected classes**

**Oregon -- SB 291 / HB 3974**
- SB 291 (2022): Requires **individualized assessment** before denial on criminal history -- algorithmic blanket denials not permitted
- HB 3974: Caps screening at **$20/applicant**

**California**: Source of Income protections (Gov. Code 12955); no algorithmic screening law yet

### E. State Laws -- AI and Employment

**Illinois BIPA** (740 ILCS 14, 2008)
- Private right of action: $1,000/negligent, $5,000/intentional violation
- **2024 Amendment (SB 2979)**: Caps at one violation per person regardless of scan count
- *Deyerler v. HireVue* (2022): BIPA class action over AI video interview biometrics -- MTD largely denied Feb 2024
- **Illinois AI Hiring Law (HB 3773)**: Bans AI hiring discrimination. Effective **January 1, 2026**

**NYC Local Law 144** (effective January 2023, enforcement July 2023)
- Annual **independent bias audits** for AEDTs; public disclosure; **10 business days** candidate notice
- Penalties: **$500-$1,500/violation/day**
- **December 2025 Comptroller Audit**: 75% of 311 calls misrouted; agency found 1 violation vs. auditors' 17+

**Colorado AI Act** (SB 24-205, signed May 2024)
- **First comprehensive state AI law** -- covers employment, housing, insurance, lending, healthcare, education
- Developers must document training data, limitations, discrimination risks
- Deployers must implement risk management, **annual impact assessments**, disclose adverse AI decisions
- Consumer rights: know when interacting with AI, correct data, appeal via **human review**
- AG exclusive enforcement; notify AG within **90 days** if discrimination found
- **Effective June 30, 2026** (delayed from Feb 2026). Rulemaking: https://coag.gov/ai/

**California CCPA/ADMT Regulations** (approved September 2025, effective January 2027)
- Most stringent U.S. rules on automated decision-making
- Pre-use notices, opt-out rights, access to outputs and logic summaries
- Mandatory risk assessments for high-risk processing

**Maryland HB 1202** (October 2020): Prohibits facial recognition in hiring without signed consent

### F. Insurance Regulation
- **23 states + D.C.** adopted NAIC AI Model Bulletin
- New York DFS requires AI doesn't proxy for protected classes
- Credit-based insurance scores **banned/restricted**: California, Hawaii, Massachusetts, Maryland

### G. EU AI Act (Entered into Force August 1, 2024)

**Prohibited (from February 2, 2025)**: Social scoring by governments or companies
**High-Risk (from August 2, 2026)**: Credit scoring, insurance risk, hiring algorithms -- not banned but must comply with risk management, transparency, human oversight, data governance
**Penalties**: Up to **35M euros or 7% global turnover** (prohibited); **15M or 3%** (high-risk)

### H. State Data Broker Laws

Four registries: **Vermont** (2018), **California** ($6,600/year fee, CPPA actively fining), **Texas** ($300 fee, WISP required), **Oregon** (2023)
**Gap**: 750+ data broker groups identified; hundreds unregistered (EFF, 2025)

### I. Federal Proposals

**Algorithmic Accountability Act of 2025** (S. 2164 / H.R. 5511): Third iteration. Impact assessments, FTC enforcement. Never advanced in prior sessions.
**No overarching federal AI law exists as of March 2026.**

### J. Can People Access Their Scores?

**Tenant screening**: Only **3% of renters** know who screened them. Trade secret claims shield logic.
**Hiring**: No right to scores. HireVue's "Candidate Insight Report" omits scores/logic/factors. California 2027 rules will be strongest.
**Insurance**: Credit-based scores accessible under FCRA. Proprietary scores largely inaccessible.

**Practical barriers**:
1. Trade secret claims shield algorithmic logic
2. Consumers don't know which company screened them
3. Dispute processes are slow -- opportunity is gone before resolution
4. Correcting underlying data may not change the predictive score
5. FCRA dispute mechanism wasn't designed for algorithmic scoring

**See [research-legal-landscape-detailed.md](research-legal-landscape-detailed.md) for full legal analysis with all URLs, phone numbers, and step-by-step processes.**

---

## 6. THE COMPANIES -- KEY PLAYERS & REVENUE

| Company | Revenue/Valuation | Market | Key Products |
|---------|-------------------|--------|-------------|
| **LexisNexis Risk Solutions** | Part of RELX Group ($43B+ market cap) | Insurance, screening, data | CLUE, Risk Classifier, consumer reports |
| **RealPage** | Acquired for **$9.6 billion** by Thoma Bravo | Tenant screening, rent pricing | AI Screening, YieldStar |
| **TransUnion** | ~$4B annual revenue | Credit, tenant screening | SmartMove, ResidentScore |
| **Upstart** | $1.04B FY2025 revenue | AI lending | Automated loan origination |
| **Zest AI** | $553.9M total funding | AI lending | Custom AI underwriting models |
| **HireVue** | $35K-$50K+/customer/year | AI hiring | Video interview analysis |
| **Eightfold AI** | Unicorn valuation | AI hiring | Talent Intelligence Platform |
| **Verisk Analytics** | ~$2.7B annual revenue | Insurance analytics | DrivingDNA, connected home data |
| **SafeRent Solutions** | Private | Tenant screening | SafeRent Score |
| **Sift** | $1B+ valuation (2021) | Digital fraud prevention | Sift Score (0-100) |
| **ChexSystems (FIS)** | Part of FIS ($40B+) | Banking account screening | QualiFile Score |
| **Appriss Retail (Retail Equation)** | Acquired by Appriss | Return fraud prevention | Return Authorization Score |
| **Kronos/UKG** | ~$14B (PE-backed) | Workforce screening | Personality/aptitude tests |
| **Workday** | ~$75B market cap | AI hiring screening | Applicant recommendation |
| **AppFolio** | ~$8B market cap | Tenant screening | FolioScreen |
| **Yardi** | Private ($8B+ est.) | Tenant screening | ScreeningWorks Pro/RentGrow |

### How They Market

- **RealPage**: "The first AI-based screening algorithm built specifically for the multifamily apartment rental industry"
- **TransUnion SmartMove**: Marketed directly to individual landlords as easy online tool
- **SafeRent**: "Mathematical analysis of information found in tenant screening reports"
- **Upstart**: "Approve 44% more creditworthy borrowers than FICO models"
- **Verisk**: Claims "12 times difference in expected losses between worst- and best-scoring groups"
- **Eightfold**: "Superior fairness and accuracy in matching people to roles" (despite class action)

### Data Collection Scale

- **LexisNexis**: **83 billion public records** on **282 million unique identities** (~290 records/person), **6+ petabytes** of data
- **Data brokers generally**: 1,000-1,500 data points per person; **Acxiom**: up to 3,000 data points per person
- **Verisk**: 260 billion miles of driving data from 8+ million vehicles
- **RealPage**: 30+ million lease outcomes for training data
- **Eightfold**: Profiles of 1 billion+ people scraped from public sources

---

## 7. WHAT CAN VIEWERS DO?

**(Full step-by-step guide with all URLs, phone numbers, and processes in [research-legal-landscape-detailed.md](research-legal-landscape-detailed.md), Part 2)**

### Request Your Tenant Screening Reports

| Company | How to Request | Phone |
|---------|---------------|-------|
| **SafeRent Solutions** | https://saferentsolutions.com/consumer-support/ -- email Consumer@SafeRentSolutions.com with disclosure request form + ID | **(888) 560-2745** (Mon-Fri 9AM-9PM ET) |
| **TransUnion SmartMove** | https://www.mysmartmove.com/ | **(866) 775-0961** |
| **CoreLogic Rental** | Mail: CoreLogic Credco, P.O. Box 509124, San Diego, CA 92150 | **(877) 532-8778** |
| **RealPage** | https://www.realpage.com/ | **(866) 934-1124** |
| **RentGrow/Yardi** | https://www.rentgrow.com/ | **(800) 736-8476** |

- One free copy every 12 months from each company under FCRA
- SafeRent delivers within 3 business days of request

### Request Your LexisNexis Reports

| Report | URL | Phone |
|--------|-----|-------|
| **Consumer Disclosure** (full data file) | https://consumer.risk.lexisnexis.com/request | **(888) 497-0011** |
| **CLUE Report** (insurance claims, 7 years) | Same portal | **(800) 456-6004** (adverse action) |

- Need: full name, address, city, zip, DOB
- One free annually under FCRA/FACT Act

### Request Other Specialty Reports

**CFPB Master List**: https://www.consumerfinance.gov/consumer-tools/credit-reports-and-scores/consumer-reporting-companies/ (lists ~40+ companies -- this is the AnnualCreditReport.com equivalent for specialty reports, but you must contact each individually)

| Report | URL | Phone |
|--------|-----|-------|
| **Credit Reports** (3 bureaus) | https://www.annualcreditreport.com/ | Free weekly |
| **ChexSystems** (banking) | https://www.chexsystems.com/ | **(800) 428-9623** |
| **NCTUE** (utilities) | https://www.nctue.com/ | **(866) 349-5185** |
| **MIB** (medical/life insurance) | https://www.mib.com/ | **(866) 692-6901** |

### Dispute Errors

1. When denied housing/job/insurance, you MUST receive an **adverse action notice** naming the screening company
2. Request your full file from that company (free within **60 days** of adverse action)
3. Review every item -- check names, dates, amounts, case dispositions
4. File formal written dispute (certified mail, keep copies)
5. Company must investigate within **30 days** and delete unverifiable items
6. Dispute BOTH with the CRA and the information furnisher (parallel investigations)
7. Willful noncompliance: **$1,000+ per violation** plus attorney's fees

**Key dispute contacts**:
- SafeRent: Consumer@SafeRentSolutions.com
- TransUnion Rental: TURSSDispute@transunion.com / **(800) 230-9376**
- CoreLogic: **(888) 333-2413**

### File Complaints

| Agency | URL | Phone |
|--------|-----|-------|
| **CFPB** | https://www.consumerfinance.gov/complaint/ | **(855) 411-2372** |
| **FTC** | https://reportfraud.ftc.gov/ | N/A |
| **HUD** (housing discrimination) | https://www.hud.gov/program_offices/fair_housing_equal_opp/online-complaint | **(800) 669-9777** |
| **EEOC** (employment) | https://www.eeoc.gov/filing-charge-discrimination | **(800) 669-4000** |
| **State AG** | Search "[your state] attorney general consumer complaint" | Varies |

- **New York AG** most active on tenant blacklisting: https://ag.ny.gov/
- **California CRD** for housing discrimination: https://calcivilrights.ca.gov/housing/
- **Colorado AG** for AI Act: https://coag.gov/ai/
- EEOC: must file within **180 days** (300 in some states)

### Opt Out of Data Broker Scores

| Broker | Opt-Out URL |
|--------|-------------|
| **LexisNexis** | https://optout.lexisnexis.com/ (10-15 min process, requires SSN, 30 days to process) |
| **Acxiom** | https://www.acxiom.com/optout/ |
| **Spokeo** | https://www.spokeo.com/optout |
| **BeenVerified** | https://www.beenverified.com/app/optout/search |
| **Whitepages** | https://www.whitepages.com/suppression-requests |

**Automated services**: DeleteMe (~$129/year), Incogni (~$6.99/month), Privacy Duck

**Critical limitation**: LexisNexis opt-out removes data from commercial sale ONLY. Data remains in FCRA-regulated products, law enforcement databases, and real-time systems. Only **6% of Americans** have ever used a data removal service. Opt-outs are partial and must be repeated.

### Request HireVue Assessment Results

- After assessment, you receive email with link to **Candidate Insight Report** (link never expires)
- **What you will NOT get**: actual assessment scores, training data, factors, logic, or techniques
- Contact the hiring company for more info (contact at bottom of report)
- You can request data deletion at any point
- **Illinois residents**: If no written BIPA consent was obtained before video interview, you may have a legal claim

### Know Your FCRA Adverse Action Rights

"Adverse action" includes more than denial -- also: higher deposit/rent, co-signer requirement, higher insurance premium, lower credit limit, higher interest rate. ALL require notice with CRA name, your dispute rights, and right to free report within 60 days. For employment: employer must provide **pre-adverse action notice** (with report copy) BEFORE final decision.

### Organizations Fighting This

| Organization | Focus | Website |
|-------------|-------|---------|
| **Algorithmic Justice League** | AI bias research, founded by Joy Buolamwini | ajl.org |
| **ACLU Racial Justice Program** | Litigates AI discrimination | aclu.org |
| **National Consumer Law Center** | Tenant screening advocacy, led SafeRent lawsuit | nclc.org |
| **Electronic Frontier Foundation** | Digital rights and privacy | eff.org |
| **Center for Democracy & Technology** | Algorithmic accountability research | cdt.org |
| **AI Now Institute** (NYU) | Algorithmic accountability policy | ainowinstitute.org |
| **Upturn** | Technology and equity research | upturn.org |
| **Electronic Privacy Information Center** | Data broker regulation | epic.org |
| **Our Data Bodies Project** | Community-centered data rights | | |
| **TechEquity Collaborative** | Housing and technology equity | techequity.us |
| **Consumer Reports** | Algorithmic transparency research | consumerreports.org |

---

## 8. NARRATIVE ARC SUGGESTIONS

### Opening Hook (60-90 seconds)

**"The Score You Never Knew You Had."** Open with a person sitting at a computer requesting their LexisNexis report for the first time, live on camera. Show their face as they scroll through pages of data they never consented to share. Cut to a montage: a family denied an apartment, a qualified applicant watching a rejection email arrive 3 minutes after submitting, an elderly patient told their coverage is cut. Title card: *"There are scores that control your life. You've never seen them. You can't appeal them. And they're almost certainly wrong."*

### Act 1: "The Invisible Architecture"

- Reveal the scale: 83 billion records, 282 million profiles, 3,000 data points per person
- Introduce Mary Louis as the emotional throughline: 16 years of perfect rent payments, denied by an algorithm
- Shock moment: 87% of criminal records in New York contain at least one error -- and these feed into instant, life-altering decisions
- Explain the key scores visually: show the SafeRent 200-800 range, the ResidentScore, the LexisNexis Risk Classifier

### Act 2: "The Machine Says No"

- Cross-cut three parallel stories:
  - **Housing**: Mary Louis / Carmen Arroyo and Mikhail (left in institution for a year because of a dismissed charge) / Marco Antonio Fernandez (Navy serviceman with top-secret clearance, confused with a cartel drug trafficker) / Glenn Patrick Thompson Sr. & Jr. (father and son left homeless because algorithm matched them to unrelated woman's eviction)
  - **Employment**: Derek Mobley (100+ rejections over 7 years, 1:50 AM rejection email) / Kyle Behm (personality test, bipolar disorder, death by suicide 2019) / D.K. (Deaf Indigenous woman told to "practice active listening" after HireVue AI failed to transcribe her speech)
  - **Insurance**: Frances Walter (cut off despite inability to walk) / Cigna (60,000 denials in one month) / Optum algorithm (200M patients affected, Black patients had 26% more chronic illness than equally-scored white patients)
- Additional victims: Kim Fuller (CFPB rejected her complaints), William Hall Jr. (falsely labeled a child sex abuser), Samantha Johnson (labeled "active inmate" in a jail she'd never been to)
- Racial disparity deep-dive: SafeRent documented discrimination, Brookings resume study (85.1% white preference), Obermeyer *Science* study on healthcare algorithm, auto insurance 70% premium gap in Black neighborhoods
- Key revelation: **67% of companies using AI hiring tools acknowledge they could introduce bias -- and use them anyway**

### Act 3: "Fighting Back"

- SafeRent settlement as turning point: $2.3M, nationwide changes
- NYC LL144 as the first attempt at regulation -- then reveal it's barely enforced (75% of complaints misrouted)
- Practical steps: show someone actually requesting their LexisNexis report, finding errors, filing disputes
- Be honest: opt-outs are partial, data gets re-collected, individual action alone is insufficient
- The systemic question: Should these scores exist at all?

### Emotional Peaks

1. **Mikhail Arroyo in the institution for a year** while his mother fought a dismissed $150 shoplifting charge in an algorithm -- he can't speak, walk, or care for himself
2. **Kyle Behm's story** -- personality test to bipolar diagnosis to suicide. The HBO documentary *Persona* released two years after his death
3. **Marco Antonio Fernandez** -- a Navy serviceman with top-secret clearance, confused with a Mexican drug trafficker by a tenant screening algorithm
4. **William Hall Jr.** -- denied a duplex in Georgia because a screening company said he sexually abused a minor. The record was for a man 30 years older who was possibly dead
5. **60,000 claims denied in one month** -- the moment viewers grasp the scale of automated human processing
6. **Mary Louis**: "I did everything right for 16 years. The algorithm didn't care."
7. **D.K.** -- a Deaf Indigenous woman with high performance scores, told by AI-generated feedback to "practice active listening" after HireVue failed to transcribe her speech
8. **Kim Fuller** -- filed complaints with the CFPB, which rejected them saying it couldn't even contact the screening company
9. **200 million patients** affected by a healthcare algorithm that concluded Black patients were healthier because they received less care

### Closing / Empowerment

Direct-to-camera or text overlay guiding viewers to request their own reports. QR codes/links to:
- LexisNexis consumer report request
- FCRA dispute instructions
- Key organizations

Final message: *"The first step to fighting a score you can't see is demanding to see it."*

Close on real footage of people going through the process -- reading reports, finding errors, filing disputes. End on collective action: the lawsuits being won, the regulations being pushed.

### Expert Voices to Interview

**Researchers**:
- **Dr. Joy Buolamwini** -- Algorithmic Justice League / MIT. Gender Shades: 34.7% error for dark-skinned women vs 0.8% for light-skinned men. Author of *Unmasking AI*
- **Cathy O'Neil** -- Author of *Weapons of Math Destruction*. Former Wall Street quant turned critic
- **Virginia Eubanks** -- Author of *Automating Inequality*. Documented algorithmic systems managing homelessness
- **Dr. Safiya Umoja Noble** -- UCLA. Author of *Algorithms of Oppression*
- **Shoshana Zuboff** -- Harvard Business School. Coined "surveillance capitalism"

**Lawyers/Advocates**:
- **Cohen Milstein attorneys** -- Led the SafeRent class action
- **NCLC staff** -- Published "Digital Denials" and led SafeRent litigation
- **Jacksonville Area Legal Aid** -- Filed 2023 SafeRent disparate impact suit

**Whistleblowers/Insiders**:
- **Christopher Wylie** -- Former Cambridge Analytica
- **Frances Haugen** -- Former Facebook/Meta

---

## KEY STATISTICS CHEAT SHEET

| Statistic | Source |
|-----------|--------|
| $1.85B tenant screening industry (2025) | Industry estimates |
| $9.6B RealPage acquisition | Thoma Bravo |
| 83 billion records on 282 million people | LexisNexis |
| 3,000 data points per person | Acxiom |
| 87% of NY criminal records contain errors | CFPB |
| 69% of arrest records missing outcome data | Consumer Reports |
| 82% of companies use AI for resumes | ResumeBuilder |
| 67% acknowledge AI bias, use it anyway | ResumeBuilder |
| 85.1% of AI resume tests prefer white names | Brookings |
| 91% of Upstart loans fully automated | Upstart |
| 60,000 insurance claims denied in one month | STAT News (Cigna) |
| 49 million claims denied in 2021 | PIRG |
| Less than 0.2% of denied claims appealed | PIRG |
| Only 3% of renters know who screened them | NCLC |
| Only 6% of Americans used data removal service | Security.org |
| Black median credit score: 612 vs White: 725 | Urban Institute |
| Black median VantageScore: 639 vs White: 730 | VantageScore (2021) |
| 26% more chronic illness in equally-scored Black patients | Obermeyer et al., *Science* (2019) |
| 200 million patients affected by biased health algorithm | Optum/UnitedHealth |
| 84% reduction in bias after algorithm fix | Obermeyer et al. |
| 70% higher auto insurance premiums in Black neighborhoods | Consumer Federation of America |
| 26,700 tenant screening complaints (2019-2022) | CFPB |
| 11,000 inaccurate background reports (2014-2019) | The Markup/NYT |
| $4.25M AppFolio FTC settlement | FTC (2020) |
| 4x rate Black students flagged "high risk" | University dropout model |
| Sift scores 1 trillion events/year, 16,000+ signals | Sift |
| 80% of U.S. banks use ChexSystems | Industry estimates |
| Zeta Global: 700M people, 2,500+ data points each | Zeta Global |
| RealPage: 13.5M rental units in pricing database | RealPage/DOJ |
| RealPage: 90% of managers approve algo price suggestions | ProPublica |
| RealPage controls 80% of revenue management software market | DOJ lawsuit |
| Verisk ClaimSearch: 1.8B claims from 95% of P&C market | Verisk |
| LexisNexis RiskView scores 80% of "unscorable" population | LexisNexis |
| Zest AI uses ~300 variables vs. credit score's 15-20 | Zest AI |
| Workday collective action: millions of applicants 40+ since 2020 | Mobley v. Workday |
| 95% of home insurers use CLUE reports | LexisNexis |
| 99%+ of auto insurers use CLUE reports | LexisNexis |

---

## KEY SOURCES

### Investigative Journalism
- ProPublica: ["How Your Shadow Credit Score Could Decide Whether You Get an Apartment"](https://www.propublica.org/article/how-your-shadow-credit-score-could-decide-whether-you-get-an-apartment) (March 2022) -- Kim Fuller, Chloe Crawford stories
- ProPublica: ["Landlords Use Secret Algorithms to Screen Potential Tenants"](https://www.propublica.org/article/landlords-use-secret-algorithms-to-screen-potential-tenants-find-out-what-theyve-said-about-you)
- ProPublica: ["Minority Neighborhoods Pay Higher Car Insurance Premiums Than White Areas With the Same Risk"](https://www.propublica.org/article/minority-neighborhoods-higher-car-insurance-premiums-white-areas-same-risk)
- The Markup: ["Access Denied: Faulty Automated Background Checks Freeze Out Renters"](https://themarkup.org/locked-out/2020/05/28/access-denied-faulty-automated-background-checks-freeze-out-renters) (May 2020) -- Thompson, Hall, Johnson stories
- The Markup: ["Can Algorithms Violate Fair Housing Laws?"](https://themarkup.org/locked-out/2020/09/24/fair-housing-laws-algorithms-tenant-screenings) (September 2020) -- Arroyo case
- NBC News: ["Tenant Screening Software Faces National Reckoning"](https://www.nbcnews.com/tech/tech-news/tenant-screening-software-faces-national-reckoning-n1260975) -- Fernandez case
- Washington Post: ["Racial Bias in Medical Algorithm Favors White Patients Over Sicker Black Patients"](https://www.washingtonpost.com/health/2019/10/24/racial-bias-medical-algorithm-favors-white-patients-over-sicker-black-patients/) (October 2019)
- Reuters/MIT Tech Review: Amazon AI Hiring Tool Bias (October 2018)
- STAT News: Medicare Advantage AI denials (NaviHealth)
- CNN: Workday AI discrimination lawsuit (May 2025)
- HR Dive: ACLU/HireVue/Intuit complaint (March 2025)

### Government/Regulatory
- FTC: "Big Data: A Tool for Inclusion or Exclusion?" (2016)
- FTC: "Data Brokers: A Call for Transparency" (2014)
- CFPB: Tenant Background Check reports (2022)
- CFPB Circulars 2022-03 and 2024-06
- HUD: AI/Fair Housing Act guidance (May 2024)
- EEOC: Title VII AI Technical Assistance (May 2023)
- White House OSTP: AI Bill of Rights -- Algorithmic Discrimination Protections

### Academic/Policy
- Obermeyer, Powers, Vogeli & Mullainathan: ["Dissecting Racial Bias in an Algorithm Used to Manage the Health of Populations"](https://www.science.org/doi/10.1126/science.aax2342), *Science* 366:447-453 (October 2019)
- Rosen, Garboden & Cossyleon: "Racial Discrimination in Housing: How Landlords Use Algorithms and Home Visits to Screen Tenants," *American Sociological Review* 86(5), 2021
- NCLC: "Digital Denials" (September 2023)
- Brookings: "Gender, Race, and Intersectional Bias in AI Resume Screening"
- Urban Institute: Credit Score Racial Disparities (2022)
- CDT: ["Tenant Screening Algorithms Enable Discrimination at Scale"](https://cdt.org/insights/tenant-screening-algorithms-enable-racial-and-disability-discrimination-at-scale-and-contribute-to-broader-patterns-of-injustice/)
- Georgetown Law Poverty Journal: ["The Discriminatory Impacts of AI-Powered Tenant Screening Programs"](https://www.law.georgetown.edu/poverty-journal/blog/the-discriminatory-impacts-of-ai-powered-tenant-screening-programs/)
- ABA Human Rights: ["Ghosts in the Machine: How Past and Present Biases Haunt Algorithmic Tenant Screening Systems"](https://www.americanbar.org/groups/crsj/resources/human-rights/2024-june/how-past-present-biases-haunt-algorithmic-tenant-screening-systems/) (June 2024)
- NBER (2021): Rental discrimination audit study -- landlords responded to white applicants 60% of the time; 5.6 pp lower for Black applicants
- FTC (2007): Credit scoring racial disparities in auto insurance
- Columbia Law Review: "Locked Out by Big Data"
- Consumer Federation of America: Auto insurance racial pricing disparities (2015)

### Books for Background
- *Weapons of Math Destruction* -- Cathy O'Neil (2016)
- *Automating Inequality* -- Virginia Eubanks (2018)
- *Algorithms of Oppression* -- Safiya Umoja Noble (2018)
- *The Age of Surveillance Capitalism* -- Shoshana Zuboff (2019)
- *Unmasking AI* -- Joy Buolamwini (2023)
