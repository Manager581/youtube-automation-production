# DETAILED LEGAL LANDSCAPE & CONSUMER ACTION GUIDE
## Supplement to Research Brief: Secret Scores

This document provides expanded legal research and specific consumer action steps to supplement Section 5 and Section 7 of the main research brief.

---

## PART 1: EXPANDED LEGAL LANDSCAPE

### A. FCRA -- Detailed Gaps for Algorithmic Scores

**What FCRA Covers (15 U.S.C. Section 1681 et seq.)**:
- Consumer reporting agencies (CRAs) must follow "reasonable procedures" to ensure "maximum possible accuracy"
- Consumers entitled to one free file disclosure per year from each CRA
- Users must provide adverse action notices naming the CRA when denying credit, housing, employment, or insurance
- Consumers have right to dispute inaccurate information; CRA must investigate within 30 days
- Limits permissible purposes for pulling consumer reports

**Critical Gaps for Algorithmic/Shadow Scores**:

1. **"Consumer Reporting Agency" Definition Gap**: Companies argue they are not CRAs because they provide "analytics" or "risk assessments" rather than traditional "consumer reports." If a company successfully argues it is not a CRA, NONE of the FCRA protections apply -- no accuracy requirements, no dispute rights, no adverse action notices.

2. **Alternative Data Gap**: FCRA was written for credit bureaus reporting loan payment history. Social media activity, app usage, shopping habits, browser history, geolocation data, and behavioral biometrics are not clearly covered. Companies using these inputs may argue their products fall outside FCRA entirely.

3. **Algorithmic Logic Protection**: Trade secret law shields the internal workings of scoring algorithms. Even when FCRA requires disclosure of "all information in the consumer's file," this has been interpreted to mean the data inputs, NOT the algorithm's logic or weighting. A consumer can see what data was used but not HOW it was weighted or WHY it produced a particular score.

4. **Dispute Mechanism Mismatch**: FCRA's dispute process was designed for factual errors ("this account isn't mine," "I paid this on time"). When the data is technically correct but the algorithm's interpretation produces a discriminatory or unfair result, the dispute process has no mechanism to challenge the scoring logic itself.

5. **Score vs. Underlying Data**: When a landlord receives only a SafeRent Score of 480, the CFPB interprets FCRA to require disclosure of the underlying data that produced that score. But in practice, many screening companies provide only the score, and enforcement of this interpretation is minimal.

6. **Rental Payment History Absent**: The CFPB found that prior rental payment history is "overwhelmingly not reflected" in tenant screening reports or algorithmic risk scores. A tenant with 16 years of on-time payments (like Mary Louis) receives no credit for that history in the algorithm.

7. **Proposed CFPB Data Broker Rule (2024)**: Would have brought data brokers under FCRA oversight for the first time. Extremely unlikely to survive the current administration's approach to the CFPB.

### B. CFPB Interpretive Rules on Algorithmic Scoring (2022-2025)

**Circular 2022-03 (May 26, 2022)** -- "Adverse action notification requirements in connection with credit decisions based on complex algorithms"
- URL: https://www.consumerfinance.gov/compliance/circulars/circular-2022-03-adverse-action-notification-requirements-in-connection-with-credit-decisions-based-on-complex-algorithms/
- Key holding: ECOA and Regulation B adverse action notification requirements apply regardless of technology used
- "A creditor's lack of understanding of its own methods is not a cognizable defense" against liability
- Creditors CANNOT use overly broad or vague reasons (e.g., "data analytics model" or "insufficient credit history")
- Must provide "specific and accurate" principal reasons even when using black-box AI/ML models
- Specificity "particularly important when creditors utilize complex algorithms, as consumers may not anticipate that certain data gathered outside of their application or credit file and fed into an algorithmic decision-making model may be a principal reason"

**Circular 2023-03 (September 19, 2023)** -- "Adverse action notification requirements and proper use of sample forms"
- URL: https://www.federalregister.gov/documents/2024/04/17/2024-08003/consumer-financial-protection-circular-2023-03-adverse-action-notification-requirements-and-proper
- Creditors using AI underwriting may NOT simply rely on the CFPB's standard model adverse action notice forms
- If the actual AI-driven reasons for denial are not captured by the standard checklist reasons, creditors must create CUSTOM reason codes
- Example: If an AI model denies someone based on "frequency of address changes correlated with default risk," that specific reason must be communicated -- not a generic "insufficient credit history"

**CFPB Innovation Spotlight (2020)** -- "Providing adverse action notices when using AI/ML models"
- URL: https://www.consumerfinance.gov/about-us/blog/innovation-spotlight-providing-adverse-action-notices-when-using-ai-ml-models/
- Acknowledged that existing framework has "built-in flexibility" compatible with AI
- Creditors CAN disclose reasons even when "the relationship of that factor to creditworthiness may be unclear to the applicant"

**CFPB Status as of March 2026**:
- In February 2025, Acting Director Russell Vought shuttered the CFPB and halted funding
- Fired approximately 1,500 of 1,700 employees
- Dropped lawsuits against Bank of America, JPMorgan Chase, Wells Fargo, Capital One
- December 30, 2025: Federal judge ruled CFPB must remain funded
- January 9, 2026: Vought requested $145 million from Federal Reserve to comply
- CFPB remains open through at least March 2026 but with drastically reduced capacity
- No new enforcement actions on algorithmic scoring are being pursued
- Advanced technology oversight page still online: https://www.consumerfinance.gov/rules-policy/advanced-technology/
- **Bottom line**: The circulars remain legally binding interpretive guidance, but there is no agency capacity to enforce them

### C. FTC Authority -- Detailed

**Section 5 Enforcement Model**:
- "Unfair" practice: (1) causes substantial injury, (2) not reasonably avoidable by consumers, (3) not outweighed by countervailing benefits
- "Deceptive" practice: material misrepresentation or omission likely to mislead reasonable consumer
- FTC CANNOT impose civil fines for first-time violations -- only injunctive relief and consent orders
- Subsequent violations of an order CAN trigger fines of up to $50,120 per violation per day

**Rite Aid Settlement (December 2023) -- Landmark Case**:
- URL: https://www.ftc.gov/news-events/news/press-releases/2023/12/rite-aid-banned-using-ai-facial-recognition-after-ftc-says-retailer-deployed-technology-without
- First FTC enforcement action addressing algorithmic bias/discrimination
- Rite Aid deployed AI facial recognition (2012-2020) in hundreds of stores
- System disproportionately generated false matches for Black, Asian, Latinx, and women consumers
- Settlement terms:
  - **5-year ban** on facial recognition for surveillance
  - Must **delete all images/photos** collected through the system
  - Must **delete all algorithms and models** developed using those images
  - Must implement safeguards before deploying any future biometric surveillance
- Algorithm deletion is the most powerful remedy -- destroys the company's investment in the biased model

**Operation AI Comply (September 2024)**:
- Enforcement sweep against five companies using AI for deceptive/unfair practices
- Included actions against fake review generators, false "AI Lawyer" services, and Evolv Technologies (false claims about AI weapons detection)

**Joint Agency Statement (April 25, 2023)**:
- FTC + CFPB + EEOC + DOJ Civil Rights Division
- URL: https://www.ftc.gov/system/files/ftc_gov/pdf/EEOC-CRT-FTC-CFPB-AI-Joint-Statement(final).pdf
- "Although many of these tools offer the promise of streamlining processes, they also have the potential to perpetuate unlawful bias, automate unlawful discrimination, and produce other harmful outcomes"

### D. State Tenant Screening Laws -- Detailed

**Washington -- Fair Tenant Screening Act (SHB 1257)**
- Codified at RCW 59.18.257
- Requires "Comprehensive Reusable Tenant Screening Reports" valid for **30 days**
- Reports must include:
  - Credit report from nationwide CRA (Equifax, Experian, or TransUnion)
  - Criminal records search from every state where applicant lived in last 7 years + sex offender registries
  - Eviction history from every state in last 7 years
- Landlords who accept portable reports CANNOT charge applicants for separate screening
- Landlord rental websites MUST state whether portable reports are accepted
- **Seattle** adds "first-in-time" screening rules: landlords must evaluate applicants in order received
- Consumer info: https://www.washingtonlawhelp.org/en/tenant-screening-your-rights
- Tenants Union info: https://tenantsunion.org/rights/tenant-screening

**Colorado -- Multiple Reforms**
- HB 23-1099: Portable Tenant Screening Reports
- HB 24-1098 (effective April 2024): "Just cause" eviction -- landlords need documented reason to evict or non-renew
- CO Revised Statutes Section 38-12-904: Limits on how rental applications are considered
- Colorado AI Act (SB 24-205): Separately covers algorithmic scoring in housing (see AI section)

**Minnesota -- SF 2087 (2025)**
- Two key prohibitions:
  1. Bans tenant screening software using **nonpublic competitor data** to set rent (directly targets RealPage-style algorithmic rent collusion)
  2. Bans background screening algorithms or AI tools with **disproportionate or arbitrary effect on protected classes** under Minnesota Human Rights Act
- **Effective August 1, 2025**
- Among the most direct state-level attacks on algorithmic tenant scoring
- Complemented by multiple 2024 tenant protection laws (effective January 1, 2025)

**Oregon -- SB 291 and HB 3974**
- SB 291 (effective January 1, 2022): Requires **individualized assessment** before denial based on criminal convictions
  - Algorithmic blanket denials based on criminal history are NOT permitted
  - Landlords must consider nature/severity of crime, time elapsed, evidence of rehabilitation
- HB 3974: Caps screening charges at **$20/applicant**, requires acceptance of third-party reports
- Oregon considering expansion of bans on algorithmic rent-setting

**California**
- Source of Income protections: Cannot discriminate against voucher holders (Gov. Code Section 12955)
- AB 1008 "Ban the Box" (2018): Prohibits criminal history questions before conditional job offer
- No specific algorithmic tenant screening law yet
- CCPA/ADMT regulations (effective 2027) will eventually cover

### E. NYC Local Law 144 -- Detailed

**Full Name**: Automated Employment Decision Tools Law
- Codified in NYC Administrative Code, Subchapter 25, Section 20-870 et seq.
- Rules: https://rules.cityofnewyork.us/rule/automated-employment-decision-tools-updated/

**Requirements**:
1. **Bias Audit**: Annual independent audit testing for disparate impact by race/ethnicity and sex/gender. Must use historical data from the tool or test data if historical unavailable
2. **Public Disclosure**: Audit results published on employer's website
3. **Candidate Notice**: 10 business days before AEDT use, must notify candidates and provide:
   - That an AEDT will be used
   - What job qualifications/characteristics the AEDT assesses
   - Data sources the AEDT uses
4. **Alternative Process**: Candidates can request alternative selection process or accommodation
5. **Data Retention**: Must comply with existing NYC data retention policies

**Penalties**: $500 first violation, $500-$1,500 each subsequent violation, per day

**December 2025 NYS Comptroller Audit Findings**:
- URL: https://www.osc.ny.gov/state-agencies/audits/2025/12/02/enforcement-local-law-144-automated-employment-decision-tools
- 75% of test calls to NYC 311 about AEDT issues were **misrouted and never reached DCWP**
- DCWP surveyed 32 companies, found just **1 non-compliance** case
- Comptroller's auditors reviewing same companies found **at least 17 potential violations**
- DCWP agreed to fix: better complaint handling, cross-trained staff, more rigorous investigations
- Employers should expect new phase of stricter enforcement with more frequent investigations

### F. Illinois BIPA and AI Hiring -- Detailed

**BIPA (740 ILCS 14)**:
- Enacted 2008, strongest biometric privacy law in the U.S.
- **Private right of action**: $1,000/negligent violation, $5,000/intentional or reckless violation
- Requires: informed written consent before collecting biometric identifiers (fingerprints, face geometry, voiceprints, iris scans)
- Must disclose: purpose of collection, length of storage, written retention/destruction policy

**2024 Amendment (SB 2979, signed August 2, 2024)**:
- Caps damages at **one violation per person** for notice-and-consent and data-disclosure claims
- Regardless of how many times that person's biometric data was collected or disclosed
- Effectively limits statutory damages to $5,000/person rather than $5,000/scan
- Major relief for defendants facing per-scan damages

**Deyerler v. HireVue (N.D. Ill., filed January 2022)**:
- Class action alleging HireVue's AI video interview technology violated BIPA
- HireVue's system analyzed facial expressions, speech patterns, non-verbal cues to assess personality/confidence
- **February 26, 2024**: Court largely denied HireVue's motion to dismiss, allowing most claims to proceed
- Significance: Employers using AI facial recognition in video interviews face BIPA liability
- Case ongoing

**Illinois AI Hiring Law (HB 3773, enacted 2024)**:
- Prohibits employers from using AI to recruit, hire, or promote if it discriminates based on protected class (race, gender, etc.)
- Requires employers to provide applicants notice when AI is used in the hiring process
- **Effective January 1, 2026**
- Broader than BIPA -- covers all AI hiring tools, not just biometric ones

### G. Colorado AI Act -- Detailed

**SB 24-205** (signed May 17, 2024)
- URL: https://leg.colorado.gov/bills/sb24-205
- AG rulemaking: https://coag.gov/ai/

**Definition of High-Risk AI System**: Any AI system that "when deployed, makes, or is a substantial factor in making, a consequential decision." A "consequential decision" has "material legal or similarly significant effect" on a consumer's life in: employment, education, financial/lending services, government services, healthcare, housing, insurance, legal services.

**Developer Obligations**:
- Make available to deployers: general statements of foreseeable uses and known harmful uses
- High-level summaries of training data
- Known limitations and risks of algorithmic discrimination
- Purpose, intended benefits, and uses
- Documentation to help deployers understand outputs and monitor performance

**Deployer Obligations**:
- Use "reasonable care" to protect consumers from known/reasonably foreseeable algorithmic discrimination risks
- Implement risk management policy and program
- Complete annual impact assessment
- Disclose to consumers: (a) they are interacting with AI (unless obvious), (b) when AI has made an adverse consequential decision
- Provide consumers: opportunity to correct incorrect personal data, right to appeal adverse decisions via human review (if technically feasible)

**Enforcement**:
- Violations = unfair trade practice under Colorado Consumer Protection Act
- **AG has exclusive enforcement authority** (no private right of action)
- Must notify AG within **90 days** of discovering algorithmic discrimination
- Affirmative defense available if deployer discovers and cures the violation
- Originally effective February 1, 2026; **delayed to June 30, 2026** after August 2025 special session

### H. EU AI Act -- Detailed

**Timeline**:
- Entered into force: August 1, 2024
- Prohibited practices apply: February 2, 2025
- General-purpose AI obligations: August 2, 2025
- High-risk AI obligations: August 2, 2026

**Prohibited (Article 5)** -- Social Scoring:
- AI systems that evaluate or classify natural persons over a certain period based on social behavior or personal/personality characteristics
- Prohibited when the resulting score leads to: detrimental or unfavourable treatment in social contexts **unrelated** to those in which the data was generated, OR treatment that is **unjustified or disproportionate** to social behavior
- Applies to both public authorities AND private companies

**NOT Prohibited but High-Risk (Article 6, Annex III)**:
- Creditworthiness assessments
- Insurance risk scoring
- Fraud detection systems
- Employment screening/hiring algorithms
- These are classified as high-risk and must comply with:
  - Risk management systems (Article 9)
  - Data governance and management (Article 10)
  - Technical documentation (Article 11)
  - Record-keeping and logging (Article 12)
  - Transparency and information to deployers (Article 13)
  - Human oversight measures (Article 14)
  - Accuracy, robustness, cybersecurity (Article 15)

**Penalties**:
- Prohibited practices: up to **35 million euros or 7% of global annual turnover** (whichever higher)
- High-risk non-compliance: up to **15 million or 3%**
- Incorrect/misleading information: up to **7.5 million or 1%**

### I. State Data Broker Laws -- Detailed

**Four states with registries**: Vermont, California, Texas, Oregon

**Vermont Data Broker Act (2018)** -- First in nation:
- Registration period: January 1-31 each year with Secretary of State
- Must disclose: data collection practices, opt-out mechanisms, data breach history, whether data sold to third parties
- No deletion right for consumers (registration/transparency only)

**California Delete Act (SB 362, signed October 2023)**:
- Amended existing data broker registration requirements
- Annual registration fee: **$6,600** (increased from previous amount)
- Fines for each day a data broker fails to register
- CPPA building centralized deletion mechanism allowing consumers to request all registered brokers delete data in one request
- California Privacy Protection Agency actively fining non-compliant brokers

**Texas (SB 2105, signed June 2023)**:
- Register with Secretary of State, pay **$300 fee**
- Must maintain Written Information Security Program (WISP):
  - Administrative, technical, and physical safeguards
  - Employee training
  - Third-party service provider policies
  - Access controls
  - Regular monitoring for unauthorized access

**Oregon (adopted rules December 2023)**:
- Similar registration requirements

**Enforcement Gap**: EFF analysis (2025) found hundreds of data brokers operating without registering. A systematic April 2025 analysis identified **750 unique data broker groups** across registries, but many more operate unregistered.

### J. Federal Proposals -- Detailed

**Algorithmic Accountability Act of 2025**:
- Senate: S. 2164 (introduced June 25, 2025)
- House: H.R. 5511
- URL: https://www.congress.gov/bill/119th-congress/senate-bill/2164/text
- Third iteration (S. 2892 / H.R. 5628 in 118th Congress; earlier versions in 117th)
- Would require covered entities using automated decision systems for consequential decisions to:
  - Conduct regular impact assessments
  - Check for discrimination and other harms
  - Document data sources and methods
  - Engage with affected communities
  - Submit summary reports to the FTC
- Covers: jobs, loans, apartments, medical care, education, essential services
- FTC enforcement authority
- None of the previous versions advanced out of committee

**Algorithm Accountability Act (Curtis/Kelly, 2025)**:
- Different bill from above despite similar name
- Senators John Curtis (R-UT) and Mark Kelly (D-AZ)
- Amends Section 230 of Communications Decency Act
- Imposes duty of care on companies using recommendation-based algorithms
- Focuses on social media platforms, not scoring systems

---

## PART 2: WHAT VIEWERS CAN DO -- DETAILED ACTION GUIDE

### Step 1: Request Your Tenant Screening Reports

**SafeRent Solutions (formerly CoreLogic SafeRent)**
- **Website**: https://saferentsolutions.com/consumer-support/
- **Email**: Consumer@SafeRentSolutions.com
- **Phone**: (888) 560-2745 (Mon-Fri, 9 AM - 9 PM ET)
- **Process**: Complete the Consumer Disclosure Request Form (available on website), email it with supporting documentation (government ID, proof of address)
- **Timeline**: Report sent within 3 business days of receiving request
- **Cost**: One free copy every 12 months
- **CFPB listing**: https://www.consumerfinance.gov/consumer-tools/credit-reports-and-scores/consumer-reporting-companies/companies-list/saferent-solutions-llc/

**TransUnion SmartMove (ResidentScore)**
- **Website**: https://www.mysmartmove.com/
- **Customer Service Phone**: (866) 775-0961
- **Dispute Phone**: (800) 230-9376 (Mon-Fri 8 AM - 8 PM ET, Sat-Sun 10:30 AM - 7 PM ET)
- **Dispute Email**: TURSSDispute@transunion.com
- **Process**: Request copies of reports you authorized. Requesting copies does NOT hurt your credit score
- **CFPB listing**: https://www.consumerfinance.gov/consumer-tools/credit-reports-and-scores/consumer-reporting-companies/companies-list/trans-union-smart-move/

**CoreLogic Rental Property Solutions**
- **Consumer Disclosure Phone**: (877) 532-8778
- **Dispute Phone**: (888) 333-2413
- **Mail**: CoreLogic Credco, LLC, P.O. Box 509124, San Diego, CA 92150
- **Alternative phone**: (800) 815-8664

**RealPage (Leasing Desk Screening)**
- **Phone**: (866) 934-1124
- **Website**: https://www.realpage.com/
- **Process**: Request consumer file disclosure under FCRA

**RentGrow/Yardi**
- **Phone**: (800) 736-8476
- **Website**: https://www.rentgrow.com/

### Step 2: Request Your LexisNexis Reports

**LexisNexis Consumer Disclosure Report** (full data file)
- **Website**: https://consumer.risk.lexisnexis.com/request
- **Phone**: (888) 497-0011
- **What you need**: First name, last name, street address, city, zip, date of birth
- **Cost**: One free report every 12 months under FCRA/FACT Act
- **What it contains**: Public records, court records, property records, driving records, and more -- this is the big one showing what LexisNexis has on you

**LexisNexis C.L.U.E. Report** (insurance claims history)
- **Same portal**: https://consumer.risk.lexisnexis.com/request
- **Adverse Action Phone**: (800) 456-6004 (if insurer sent adverse action letter)
- **What it contains**: Up to 7 years of auto insurance claims + 7 years of home/property insurance claims
- **Cost**: One free annually
- **Why it matters**: Insurers use CLUE data to set rates and deny coverage. Errors can follow you for years

**LexisNexis Accurint Person Report** (law enforcement/investigative)
- This is a separate product used by law enforcement and investigators -- harder to access but you can request your file

### Step 3: Request Your Other Specialty Reports

**CFPB Master List of Consumer Reporting Companies**:
- **2025 List**: https://files.consumerfinance.gov/f/documents/cfpb_consumer-reporting-companies_list_2025.pdf
- **Portal**: https://www.consumerfinance.gov/consumer-tools/credit-reports-and-scores/consumer-reporting-companies/
- Lists approximately 40+ companies with websites and phone numbers
- This is the closest thing to an AnnualCreditReport.com for specialty reports -- but you must contact each company individually

**Key Specialty Reports to Request**:
1. **Credit Reports**: AnnualCreditReport.com (all 3 bureaus, free weekly)
2. **ChexSystems** (banking): https://www.chexsystems.com/ -- (800) 428-9623
3. **NCTUE** (utility payment history): https://www.nctue.com/ -- (866) 349-5185
4. **MIB** (medical/life insurance): https://www.mib.com/ -- (866) 692-6901
5. **Innovis** (4th credit bureau): https://www.innovis.com/ -- (800) 540-2505

### Step 4: Opt Out of Data Broker Scores

**LexisNexis Opt-Out**:
- **URL**: https://optout.lexisnexis.com/
- **Process**: Enter email, agree to terms, enter full information including SSN, search for your listing, click "Remove this record," confirm
- **Time**: Takes 10-15 minutes. Processing takes up to 30 days
- **Critical limitation**: Opt-out removes data from commercial sale products ONLY. Your data REMAINS in: FCRA-regulated products, law enforcement databases, real-time verification systems
- **Consumer access policies**: https://risk.lexisnexis.com/consumer-and-data-access-policies

**Acxiom Opt-Out**:
- **URL**: https://isapps.acxiom.com/optout/optout.aspx (or https://www.acxiom.com/optout/)
- **Process**: Submit your information for removal from marketing products

**Other Major Data Broker Opt-Outs**:
- **Spokeo**: https://www.spokeo.com/optout
- **BeenVerified**: https://www.beenverified.com/app/optout/search
- **Whitepages**: https://www.whitepages.com/suppression-requests
- **PeopleFinder**: https://www.peoplefinder.com/optout.php
- **Intelius**: https://www.intelius.com/opt-out

**Automated Opt-Out Services** (paid):
- **DeleteMe**: https://joindeleteme.com/ (~$129/year)
- **Incogni**: https://incogni.com/ (~$6.99/month)
- **Privacy Duck**: https://www.privacyduck.com/
- These services automate opt-out requests across dozens of brokers and monitor for re-listing

**Reality Check**: Only **6% of Americans** have ever used a data removal service. Opt-outs are partial, temporary, and must be repeated as data is continuously re-collected from public records and commercial sources.

### Step 5: Dispute Errors in Screening Reports

**Your FCRA Rights When Denied**:

When you are denied housing, employment, insurance, or credit based on a consumer report, the entity MUST provide you with an **adverse action notice** that includes:
1. **Notice of the action taken** (denial, higher rate, etc.)
2. **Name, address, and phone number** of the CRA that supplied the report
3. **Statement that the CRA did not make the decision** and cannot explain why
4. **Notice of your right to dispute** accuracy/completeness of any information
5. **Notice of your right to a free report** from that CRA within 60 days

**How to Dispute**:
1. Request your full file from the CRA named in the adverse action notice (free within 60 days)
2. Review every item for accuracy -- check names, dates, amounts, case dispositions, addresses
3. Write a formal dispute letter identifying each error specifically
4. Send disputes by certified mail (keep copies of everything)
5. The CRA must investigate within **30 days** (45 days if you provide additional information)
6. The CRA must forward your dispute to the information furnisher (landlord, court, etc.)
7. The furnisher must investigate and report back
8. If the item cannot be verified, it must be **deleted**
9. You must be notified of the results

**Dispute Contacts**:
- SafeRent: Consumer@SafeRentSolutions.com
- TransUnion Rental Screening: TURSSDispute@transunion.com or (800) 230-9376
- CoreLogic: (888) 333-2413
- For credit reports: Each bureau has online dispute portals

**Key tip**: If you find errors, dispute BOTH with the CRA and directly with the information furnisher (the company that provided the data). This creates two parallel investigations.

**Willful noncompliance penalty**: The greater of actual damages or **$1,000 per violation**, plus attorney's fees. If a CRA willfully violates FCRA, consumers can sue.

### Step 6: File Complaints

**CFPB Complaint Portal**:
- **URL**: https://www.consumerfinance.gov/complaint/
- **Phone**: (855) 411-CFPB (855-411-2372)
- **What to file about**: Errors in tenant screening reports, failure to provide adverse action notices, failure to investigate disputes, inaccurate scoring
- **Note**: CFPB capacity is severely reduced as of March 2026 but the complaint portal remains operational. Complaints create a public record even if enforcement is delayed
- **CFPB analyzed 24,000+ tenant screening complaints** in its 2022 report: 16,000+ about incorrect information, 4,500+ about obstacles fixing errors

**FTC Complaint**:
- **URL**: https://reportfraud.ftc.gov/
- **What to file about**: Deceptive practices, unfair algorithmic scoring, discrimination by AI systems
- FTC does not resolve individual complaints but uses them to identify patterns for enforcement

**State Attorney General Complaints**:
- Every state AG has a consumer complaint process. File with your state AG when:
  - A company fails to provide adverse action notice
  - A screening company won't investigate your dispute
  - You believe algorithmic discrimination occurred
- **New York**: AG has been most active -- tenant blacklisting complaint form online at https://ag.ny.gov/
- **California**: Civil Rights Department handles housing discrimination: https://calcivilrights.ca.gov/housing/
- **Colorado**: AG office handles AI Act complaints: https://coag.gov/ai/

**HUD Fair Housing Complaint**:
- **URL**: https://www.hud.gov/program_offices/fair_housing_equal_opp/online-complaint
- **Phone**: (800) 669-9777
- **What to file about**: Housing discrimination, including discrimination by algorithmic screening tools
- HUD's May 2024 guidance clarified that housing providers, screening companies, and ad platforms can all be liable under Fair Housing Act for algorithmic discrimination

**EEOC Complaint** (employment):
- **URL**: https://www.eeoc.gov/filing-charge-discrimination
- **Phone**: (800) 669-4000
- **What to file about**: Discriminatory hiring algorithms, AI-based employment screening that has disparate impact
- Must file within 180 days of discriminatory act (300 days in states with fair employment agencies)

### Step 7: Request Your HireVue Assessment Results

- After your assessment is processed and insights calculated, you receive an email with a hyperlink to view your **Candidate Insight Report**
- This link never expires -- save it
- Only you and the hiring company can see the results unless you share them
- **What you WON'T get**: HireVue does NOT give candidates access to:
  - Their actual assessment scores
  - The training data used
  - The factors, logic, or techniques that generated the assessment
  - How your responses were weighted
- **To get more information**: Contact the company that interviewed you (contact info appears at bottom of your report if provided)
- **To delete your data**: You can request deletion at any point, but HireVue says the hiring company (not HireVue) decides whether and when to delete
- **For BIPA claims** (Illinois residents): If you were not informed in writing before the video interview that your biometric data would be collected and did not sign a consent, you may have a BIPA claim. Consult an attorney

### Step 8: Know Your Rights Under FCRA Adverse Action Notices

**For Housing Denials**:
- Landlord MUST give you written notice including:
  - The screening company's name, address, and phone number
  - Your right to get a free copy of the report within 60 days
  - Your right to dispute any inaccurate information
  - Statement that the CRA did not make the denial decision
- If a landlord denies you and does NOT provide this notice, they are violating FCRA
- Penalty for willful noncompliance: $1,000+ per violation plus attorney's fees

**For Employment Denials**:
- Employer must provide **pre-adverse action notice** BEFORE final decision (giving you a chance to respond)
- Must include copy of the consumer report and a "Summary of Rights under FCRA"
- After waiting a reasonable time, employer provides **final adverse action notice**
- Same disclosure requirements as housing

**For Insurance Denials/Rate Increases**:
- Insurer must provide notice if adverse action is based wholly or partly on consumer report
- Must name the CRA, provide right to free report within 60 days
- For credit-based insurance scores: must disclose the score and key factors

**What "Adverse Action" Includes** (broader than many think):
- Denial of application
- Higher deposit or rent
- Requirement for a co-signer
- Higher insurance premium
- Lower credit limit
- Higher interest rate
- Requirement for additional conditions

---

## PART 3: KEY SOURCES AND URLS

### Government/Regulatory URLs
| Resource | URL |
|----------|-----|
| CFPB Complaint Portal | https://www.consumerfinance.gov/complaint/ |
| CFPB Consumer Reporting Companies List | https://www.consumerfinance.gov/consumer-tools/credit-reports-and-scores/consumer-reporting-companies/ |
| CFPB Circular 2022-03 (Algorithmic Adverse Action) | https://www.consumerfinance.gov/compliance/circulars/circular-2022-03-adverse-action-notification-requirements-in-connection-with-credit-decisions-based-on-complex-algorithms/ |
| FTC Complaint Portal | https://reportfraud.ftc.gov/ |
| FTC Rite Aid Settlement | https://www.ftc.gov/news-events/news/press-releases/2023/12/rite-aid-banned-using-ai-facial-recognition-after-ftc-says-retailer-deployed-technology-without |
| HUD Fair Housing Complaint | https://www.hud.gov/program_offices/fair_housing_equal_opp/online-complaint |
| EEOC Charge Filing | https://www.eeoc.gov/filing-charge-discrimination |
| AnnualCreditReport.com | https://www.annualcreditreport.com/ |
| Colorado AI Act Rulemaking | https://coag.gov/ai/ |
| NYC LL144 Rules | https://rules.cityofnewyork.us/rule/automated-employment-decision-tools-updated/ |
| EU AI Act | https://artificialintelligenceact.eu/ |
| Algorithmic Accountability Act (S. 2164) | https://www.congress.gov/bill/119th-congress/senate-bill/2164/text |

### Consumer Report Request URLs
| Company | URL / Phone |
|---------|------------|
| LexisNexis Consumer Disclosure | https://consumer.risk.lexisnexis.com/request / (888) 497-0011 |
| LexisNexis CLUE (insurance) | https://consumer.risk.lexisnexis.com/request / (800) 456-6004 |
| LexisNexis Opt-Out | https://optout.lexisnexis.com/ |
| SafeRent Solutions | https://saferentsolutions.com/consumer-support/ / (888) 560-2745 |
| TransUnion SmartMove | https://www.mysmartmove.com/ / (866) 775-0961 |
| TransUnion Rental Disputes | TURSSDispute@transunion.com / (800) 230-9376 |
| CoreLogic Rental | (877) 532-8778 / Disputes: (888) 333-2413 |
| Acxiom Opt-Out | https://www.acxiom.com/optout/ |
| ChexSystems (banking) | https://www.chexsystems.com/ / (800) 428-9623 |
| NCTUE (utilities) | https://www.nctue.com/ / (866) 349-5185 |
| MIB (medical/life insurance) | https://www.mib.com/ / (866) 692-6901 |

### State AG Complaint Resources
| State | Resource |
|-------|----------|
| New York | https://ag.ny.gov/ (tenant blacklisting complaints) |
| California | https://calcivilrights.ca.gov/housing/ (housing discrimination) |
| Colorado | https://coag.gov/ai/ (AI Act complaints) |
| Washington | https://www.washingtonlawhelp.org/en/tenant-screening-your-rights |
| General | Search "[your state] attorney general consumer complaint" |
