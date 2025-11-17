# Clinical Decision Support Systems (CDSS) & AI-Powered Interventions: A Comprehensive Literature Review

**Date:** November 2025
**Focus:** Understanding effective design and implementation of AI interventions to reduce low-value care at the point of care

---

## Executive Summary

Clinical Decision Support Systems (CDSS) represent a critical intersection of healthcare delivery and health information technology, with the potential to significantly improve patient outcomes, reduce medical errors, and decrease low-value care. This literature review synthesizes current evidence on CDSS effectiveness, design principles, and implementation strategies, with particular emphasis on AI/ML-powered interventions delivered at the point of care.

### Key Findings:

1. **Effectiveness Evidence**: CDSS demonstrate moderate evidence for improving practitioner performance (52-66% of studies show positive effects) and patient outcomes (30-61% show benefits), particularly in medication safety, chronic disease management, and guideline adherence.

2. **Alert Fatigue Crisis**: High override rates and alert fatigue represent the most significant barrier to CDSS effectiveness. Clinicians process an average of 56 alerts per day, spending 49 minutes daily on alert management, with many alerts being irrelevant or duplicative.

3. **Workflow Integration is Critical**: CDSS integrated into clinical workflows rather than requiring separate logins or screens show significantly higher adoption and effectiveness. Standalone systems that disrupt workflow face major barriers to acceptance.

4. **AI/ML Promise and Challenges**: Machine learning-based CDSS show improved diagnostic accuracy and earlier intervention compared to rule-based systems, but face significant challenges in explainability, trust, and real-world deployment. The "black box" problem remains a major barrier to clinical adoption.

5. **The Five Rights Framework**: Successful CDSS deliver the right information, to the right person, in the right format, through the right channel, at the right time in workflow—a framework that should guide all CDSS development.

6. **Interruptive vs. Non-Interruptive**: Interruptive alerts are more effective but contribute to alert fatigue and workflow disruption. Best practice suggests reserving interruptive alerts for only critical situations while using passive/non-interruptive support for less urgent recommendations.

7. **Implementation Success Factors**: User-centered design, effective governance structures, role-based alert distribution, regular monitoring of alert response rates, and maintaining up-to-date clinical knowledge bases are essential for successful implementation.

### Critical Gaps:

- Limited high-quality evidence on ML-based CDSS impact on clinical outcomes in real-world settings
- Insufficient research on optimal timing and delivery mechanisms for different types of interventions
- Need for better evaluation frameworks that assess both system accuracy and impact on end-user performance
- Limited understanding of how to effectively reduce low-value care through CDSS at scale

---

## 1. Evolution of Clinical Decision Support Systems

### 1.1 Definition and Scope

Clinical Decision Support Systems are health information technology systems designed to assist clinicians with decision-making tasks at the point of care. According to AHRQ, CDSS provide "clinicians, staff, patients, or other individuals with knowledge and person-specific information, intelligently filtered or presented at appropriate times, to enhance health and health care."

CDSS encompass a wide range of tools including:
- Computerized alerts and reminders
- Clinical guidelines and care pathways
- Order sets and protocols
- Diagnostic support systems
- Focused patient data reports
- Documentation templates
- Reference information and literature databases

### 1.2 Historical Evolution: From Rule-Based to AI/ML Systems

#### **Generation 1: Rule-Based CDSS (1960s-2000s)**

The earliest CDSS were knowledge-based systems using IF-THEN rules derived from clinical guidelines and expert knowledge. These systems were characterized by:

**Strengths:**
- Transparent and easy to audit
- Explainable decision-making process
- Direct mapping to clinical guidelines
- Deterministic and reproducible outputs

**Limitations:**
- Brittle systems struggling with edge cases and missing data
- Difficulty scaling to handle complex, multifactorial conditions
- Labor-intensive maintenance of rule bases
- Inability to learn from new data or adapt to changing patterns
- Limited ability to personalize recommendations

**Clinical Impact:**
Rule-based CDS demonstrated effectiveness in improving care delivery (57% of studies) and patient outcomes (30% of studies), particularly in drug ordering and preventive care. However, the need for constant manual updates to keep pace with evolving medical knowledge proved challenging even for well-resourced institutions.

#### **Generation 2: Non-Knowledge-Based CDSS Using AI/ML (2010s-Present)**

Modern CDSS increasingly leverage artificial intelligence, machine learning, and statistical pattern recognition:

**Key Technologies:**
- Neural networks and deep learning
- Natural language processing (NLP)
- Decision trees and random forests
- Support vector machines
- Ensemble methods

**Advantages Over Rule-Based Systems:**
- Ability to learn from large-scale patient data
- Identification of complex, non-linear patterns
- Continuous improvement with new data
- Handling of incomplete or ambiguous information
- Potential for earlier intervention and improved diagnostic accuracy

**Comparative Performance:**
ML-based CDSS have demonstrated:
- Improved diagnostic accuracy compared to clinical assessment tools (SIRS, SOFA, MEWS scores)
- Earlier detection of clinical deterioration (e.g., sepsis prediction)
- Reduced false positives in some applications
- Enhanced ability to personalize treatment recommendations

**Current Limitations:**
- "Black box" problem—difficulty understanding AI decision-making logic
- Limited explainability undermines clinician trust
- Data availability and quality requirements
- Challenges with bias and generalization across populations
- Limited real-world deployment and validation
- Regulatory and liability concerns
- Integration complexity with existing EHR systems

**Evidence of Effectiveness:**
Of 23 ML-based CDSS studies examined in recent systematic reviews:
- 5 showed improvements in care delivery (faster treatment, increased preventive orders)
- 6 demonstrated enhanced patient outcomes (higher case finding, shorter hospital stays, lower mortality)
- Mixed results overall, with significant heterogeneity

#### **Generation 3: Hybrid and Context-Aware Systems (Emerging)**

The latest generation combines rule-based and ML approaches with:
- Context-aware computing that senses and reacts to environmental factors
- Integration of genomic and precision medicine data
- Real-time learning and adaptation
- Multi-modal data integration (structured EHR, unstructured notes, imaging, wearables)
- Explainable AI (XAI) techniques to address the black box problem

### 1.3 Current Adoption Landscape

**Prevalence:**
- 2013: 41% of U.S. hospitals with EHR had CDSS capability
- 2017: 40.2% of U.S. hospitals had advanced CDS capability (HIMSS Stage 6)
- 2013-2014: EHR adoption increased from 59% to 97% for hospitals and 48% to 74% for office-based physicians, driven by meaningful use requirements

**FDA Regulation:**
As of July 2024, the FDA database included 882 AI- and ML-enabled medical devices across various specialties, indicating rapid growth in commercial AI-CDSS products.

---

## 2. Evidence of CDSS Effectiveness

### 2.1 Overall Impact on Healthcare Delivery

**Systematic Review Findings:**

Multiple systematic reviews provide evidence of CDSS effectiveness across various domains:

**Practitioner Performance:**
- 52% of studies measuring process of care showed statistically significant improvement
- 66% of articles reported positive practitioner performance (more recent reviews)
- Significant improvements in guideline adherence, ranging from 16-35% depending on therapy

**Patient Outcomes:**
- 31% of trials measuring patient outcomes demonstrated benefits (earlier reviews)
- 61% showed positive patient medical outcomes (more recent reviews)
- Benefits include reduced mortality, shorter hospital stays, fewer complications

**Key Success Domains:**
1. Medication ordering and safety
2. Preventive care reminders
3. Chronic disease management
4. Diagnostic accuracy
5. Guideline adherence

### 2.2 Medication Safety and Adverse Drug Event Prevention

CDSS demonstrate the strongest evidence base in medication-related applications:

**Medication Error Prevention (Moderate Evidence):**
- CPOE with medication-related CDSS associated with reduced medication errors
- Improved targeting of medication-related CDSS associated with reductions in medication errors and adverse drug events
- 44% of medication errors would have been missed without CDS (Raschke et al.)

**Adverse Drug Event Prevention (Low to Very Low Evidence):**
- Some evidence of reduced adverse drug events, though certainty of evidence remains low
- CPOE+CDSS effective at reducing prescribing errors but unclear evidence for reducing clinical ADEs in inpatient or outpatient settings
- CDS systems with automated alerts demonstrate efficacy for detecting medication errors and ADEs

**Specific Applications:**
- Drug-drug interaction alerts
- Dose optimization based on renal function
- Allergy checking
- Duplicate therapy detection
- High-risk medication monitoring

**Challenges:**
- High override rates (varies by study)
- Alert fatigue from excessive notifications
- Irrelevant or mistimed alerts
- Average of 56 alerts per clinician per day, requiring 49 minutes daily to process

### 2.3 Chronic Disease Management

**Diabetes Management:**
A systematic review of antidiabetic drug prescription found that 9 studies demonstrated positive impacts including:
- Reduction in inappropriate prescriptions
- Decreased hypoglycemia events
- Improved glycemic control
- Better adherence to treatment guidelines

**Cardiovascular Disease:**
- CDSS for atrial fibrillation increased guideline adherence for anticoagulant therapy
- Cardiac care CDSS associated with 16-35% increases in guideline adherence
- Clinical decision support for heart failure showed reduced exacerbations and mortality

**Chronic Kidney Disease:**
- Guideline-based CDSS improved laboratory monitoring adherence
- Enhanced achievement of laboratory targets in stage 3-4 CKD patients
- Better medication dosing adjustments

**Respiratory Conditions:**
CDSS for COPD, asthma, and heart failure in adults reported:
- Reduced exacerbations
- Improved quality of life
- Better patient-reported outcomes
- Reduced mortality

**Key Barrier:** Low usage rates emerged as the main barrier to effectiveness in respiratory condition management.

### 2.4 Sepsis Detection and Early Warning Systems

Sepsis represents a critical application area for ML-based CDSS:

**Effectiveness Evidence:**
- Cloud-based sepsis CDS integrated with EHR described as effective for early recognition
- Machine learning-based early warning systems associated with better patient outcomes including reduced in-hospital mortality
- High rates of healthcare provider interaction with ML-based sepsis alerts
- Faster antibiotic ordering when systems used

**Performance Advantages:**
- Earlier identification of at-risk patients compared to traditional scoring systems
- Most powerful impact: identifying patients where providers had not yet recognized SIRS or sepsis
- ML models demonstrated improved diagnostic accuracy vs. SIRS, SOFA, and MEWS scores

**Challenges:**
- Poor consensus on effectiveness in improving health outcomes
- Barriers include poor diagnostic accuracy (in some implementations)
- Poor implementation strategies
- Clinician mistrust
- High false positive rates in some systems

**Most Reported Outcome:** Mortality was the most frequently reported patient outcome (60% of 65 studies in scoping review)

### 2.5 Diagnostic Accuracy and Decision-Making

**BMJ Best Practice Integration:**
Peking University Third Hospital study showed:
- 75.46% accuracy for first-rank diagnosis
- 87.53% accuracy for top-3 diagnosis
- Reduced confirmed diagnosis times
- Shorter hospitalization days

**Limitations:**
- Diagnostic accuracy alone does not ensure improved clinical outcomes
- Integration into workflow and clinician acceptance remain critical
- Need for systems that support rather than replace clinical judgment

### 2.6 Reducing Low-Value Care and Inappropriate Utilization

CDSS show promise in addressing overuse and low-value care:

**Imaging Utilization:**
Virginia Mason Medical Center interventional CDS:
- Substantially decreased lumbar MRI utilization for low back pain
- Reduced head MRI for headache
- Decreased sinus CT for sinusitis
- Required providers to answer appropriateness questions before ordering

**Laboratory Testing:**
- "Hard Stop" interventions requiring justification for duplicate tests reduced unnecessary testing
- "Smart Alert" notifications also effective but less so than hard stops
- Requiring explicit evidence-based rationale for vitamin D screening dramatically reduced overuse

**Broader Context:**
- Estimated 30% of healthcare spending on unnecessary, wasteful, or harmful care
- CDSS can improve adherence to guidelines for diagnostic imaging
- Potential to identify high-risk patients and prevent unnecessary procedures
- Integration with Choosing Wisely recommendations

**De-Implementation Targets:**
- Duplicative lab testing
- Unnecessary blood transfusion volumes
- Inappropriate indwelling catheter use
- Antibiotic overuse in ICU
- Unnecessary imaging

---

## 3. Common Failure Modes and Solutions

### 3.1 Alert Fatigue: The Primary Threat to CDSS Effectiveness

**Problem Scope:**

Alert fatigue represents the most significant barrier to CDSS success and is characterized by:
- High volume of alerts (average 56 per clinician per day)
- Time burden (49 minutes daily processing alerts)
- High override rates (varies widely but often >90% for certain alert types)
- Desensitization to all alerts, including critical ones
- Increased cognitive load and workflow disruption

**Root Causes:**
1. Excessive number of alerts
2. High proportion of uninformative or irrelevant alerts
3. Lack of context-specificity
4. Repeated alerts for the same issue (within-patient repeats)
5. Poor alert prioritization
6. Alerts that encroach on perceived physician autonomy
7. Mistrust of alert information
8. Outdated clinical knowledge in alerts

**Consequences:**
- Reduced effectiveness of legitimate alerts
- Patient safety risks from missed critical alerts
- Clinician burnout and frustration
- Decreased system acceptance and adoption
- Return to pre-CDSS practice patterns

### 3.2 Mitigation Strategies for Alert Fatigue

**1. Alert Classification and Tiering**

**Approach:** Organize alerts into severity levels (severe, moderate, minor) with only critical alerts being interruptive.

**Evidence:**
- Three-tier system with active and passive groups
- Core set of critical drug-to-drug interactions
- Only critical alerts should interrupt workflow
- Less critical alerts should be non-interruptive and accessible on demand

**Recommendation:** Reserve interruptive alerts for truly critical situations where immediate action prevents serious harm.

**2. Role-Based Alert Distribution**

**Approach:** Direct alerts to the most appropriate healthcare professional rather than defaulting to physicians.

**Evidence:**
- Shifting time-dependent drug interaction alerts to nurses reduced incorrect administration times by 29%
- Semi-automated systems sending alerts to clinical pharmacists for review before reaching physicians effective in limiting alert burden
- Pharmacist-mediated review filters out non-actionable alerts

**Benefit:** Reduces physician alert burden while ensuring appropriate clinical review.

**3. Reducing Repeated Alerts**

**Approach:** Eliminate within-patient repeats for acknowledged alerts; implement time-based suppression.

**Evidence:**
- Reducing within-patient repeats identified as promising target for reducing alert overrides
- Alert fatigue caused by combination of uninformative alerts and repeated presentations
- High override rates partially due to seeing same alert multiple times for one patient

**Implementation:** Track alert acknowledgment and suppress repeats for defined time periods unless clinical context changes.

**4. Improved Interaction Design**

**Approaches:**
- Tiering alerts to convey risk level visually
- Clear, concise alert messages with specific actionable recommendations
- Minimal clicks required to act on or dismiss alerts
- Context-sensitive presentation
- Integration of alerts within workflow rather than pop-ups
- Questions within orders to guide decision-making (instead of alerts)
- Organized order collections and template fields

**Evidence:**
- Alternative interactive designs can reduce alert fatigue
- Medication safety alert fatigue may be reduced via interaction design and clinical role tailoring
- Decision support can be implemented outside traditional alerting

**5. Ongoing Monitoring and Governance**

**Essential Components:**
- Regular monitoring of alert response rates
- Analysis of override patterns and reasons
- Continuous refinement based on usage data
- User training on system improvements
- Regular review of alert appropriateness
- Sunset policies for low-value alerts

**Organizational Responsibility:** Effective governance structures with clinical and technical representation essential for maintaining alert quality.

### 3.3 Poor Workflow Integration

**Problem:**

Historically, CDSS workflow integration represents one of the largest barriers to acceptance:

**Common Issues:**
- Stand-alone applications requiring separate login
- Need to cease work in current system to access CDSS
- Re-entry of data already documented elsewhere
- Interruptions that break clinical flow and cost time
- Design without consideration of human information processing
- Poor timing of interventions relative to clinical workflow

**Impact:**
- Clinician resistance and low adoption
- Workarounds that bypass system
- Incomplete or inconsistent usage
- Failure to realize intended benefits

**Solutions:**

**1. Integration into Native Workflow**
- Embed in existing EHR without separate login or screen
- Single-click or zero-click access to recommendations
- Automatic population from existing EHR data
- Presentation at natural decision points

**Evidence:** Integration into clinical workflows (vs. separate logins) strongly associated with CDSS success.

**2. Timing and Location**
- Deliver support at time and location of care rather than before
- Align with natural clinical workflow steps
- Just-in-time information delivery
- Right information, right time (Five Rights framework)

**3. Minimize Additional Work**
- Auto-populate data from EHR
- One-click order sets rather than manual order entry
- Standing orders integrated into IT systems
- Streamlined documentation

**Evidence:** Standing orders generally more effective than reminders.

### 3.4 Lack of Clinician Trust and Acceptance

**Barriers to Trust:**

**For Traditional CDSS:**
- Concerns about clinical accuracy and appropriateness
- Perception that alerts encroach on professional autonomy
- Mistrust of alert information
- Preference for senior staff or departmental guidelines over system recommendations
- Fear that using CDSS raises doubts about professionalism

**For AI/ML-Based CDSS:**
- Opacity of "black box" decision-making
- Inability to explain AI reasoning
- Fear of algorithmic bias
- Concern about technology replacing human judgment
- Questions about liability when following AI recommendations
- Professional identity threat

**Impact:**
- Low adoption rates
- High override rates even for appropriate alerts
- Return to pre-intervention practices after research period ends
- Rejection of AI-based systems

**Solutions:**

**1. Explainability and Transparency**
- Use inherently interpretable algorithms when possible (decision trees, logistic regression)
- Implement explainable AI (XAI) techniques for black box models (SHAP, LIME)
- Provide clear rationale for recommendations
- Show supporting evidence and guideline references
- Indicate confidence levels

**Trade-off Consideration:** Simpler, more explainable models may sacrifice some predictive power of complex neural networks. Context-dependent analysis needed to determine appropriate balance.

**2. User-Centered Design**
- Involve clinicians throughout development process
- Iterative design based on user feedback
- Ethnographic research to understand clinical context
- Cognitive science-based HCI methods
- Testing with representative end-users

**Evidence:** User-centered design critical for CDSS effectiveness and adoption, though resource-intensive.

**3. Appropriate Positioning**
- Frame as decision support, not decision replacement
- Emphasize augmentation of clinical judgment
- Preserve physician autonomy and final decision authority
- Avoid mandatory compliance with recommendations
- Position as tool to enhance, not question, expertise

**4. Demonstration of Value**
- Share outcome data showing benefit
- Provide feedback on positive impacts
- Transparent reporting of system performance
- Acknowledge and address failures
- Continuous quality improvement based on real-world performance

### 3.5 Inadequate Clinical Knowledge Maintenance

**Problem:**

Even advanced healthcare institutions report difficulty keeping CDSS knowledge bases current with:
- Fast-changing medical practice
- Evolving clinical guidelines
- New evidence and drug approvals
- Updated safety information

**Consequences:**
- Outdated recommendations
- Missed opportunities for improved care
- Clinician mistrust when they recognize outdated content
- Alert fatigue from alerts based on superseded guidelines

**Solutions:**

**1. Governance Structures**
- Committees to oversee knowledge base updates
- Clear ownership and accountability
- Clinical and technical representation
- Regular review cycles
- Integration with guideline update processes

**2. Systematic Update Processes**
- Subscription to guideline update services
- Monitoring of FDA safety communications
- Review of relevant literature
- Stakeholder notification of pending changes
- Version control and change documentation

**3. Content Management Systems**
- Centralized knowledge repositories
- Standardized representation of clinical rules
- Reusable modules across applications
- Automated testing of rule changes
- Impact analysis before deployment

### 3.6 Poor EHR Integration and Interoperability

**Technical Challenges:**

**Proprietary Development Environments:**
- CDS tools typically built using EHR's proprietary platform
- Limited by EHR functionality, often rudimentary
- Need to rebuild tools independently for each different EHR
- Significant barriers to scalability

**Data Challenges:**
- Programming complexities
- Diversity of clinical data sources
- Inconsistent data quality
- Different clinical terminologies and languages
- Missing or incomplete data

**Integration Issues:**
- Concerns about transporting sensitive patient information
- Lack of interoperability between tools and EHR systems
- Difficulty accessing real-time data
- Complex interfaces and APIs

**Solutions:**

**1. Standards-Based Development**
- Use of FHIR (Fast Healthcare Interoperability Resources)
- HL7 standards for clinical decision support
- Standard clinical terminologies (SNOMED, LOINC, RxNorm)
- Interoperable CDS artifacts (CQL, CDS Hooks)

**2. Platform-Based Approaches**
- Novel platforms that abstract from specific EHR implementations
- Middleware solutions for EHR integration
- Cloud-based CDS services
- Reduced need for EHR-specific customization

**3. Data Quality Programs**
- Structured data capture where possible
- NLP for extracting information from unstructured notes
- Data validation and completeness checks
- Feedback to clinicians on documentation quality

### 3.7 Insufficient Evidence Generation and Evaluation

**Problems:**

**Focus on System Accuracy:**
- Evaluation processes emphasize system accuracy metrics
- Overlook system impact on process outcomes
- Limited assessment of end-user performance
- Insufficient measurement of real-world effectiveness

**Heterogeneity:**
- Wide variation in CDSS types, settings, and outcomes measured
- Difficult to synthesize evidence across studies
- Limited comparability between interventions
- Unclear which specific features drive effectiveness

**Research-Practice Gap:**
- Most ML-based CDSS research in controlled simulation settings
- Limited real-world deployment and validation
- Challenges applying research findings to complex clinical environments
- After research support removed, clinicians often return to pre-study practices

**Solutions:**

**1. Comprehensive Evaluation Frameworks**
- Measure net benefit across four categories:
  - Process of care
  - Professional competency
  - Patient outcomes
  - Cost-effectiveness
- Include technology performance, behavioral impact, and clinical outcomes
- Use established models (DeLone & McLean, ISO standards)
- Five-stage evaluation including post-deployment surveillance

**2. Patient-Centered Outcomes**
- Patient activation and engagement
- Patient satisfaction
- Shared decision-making
- Patient knowledge acquisition
- Patient-relevant outcomes
- Decisional quality

**3. Real-World Deployment Studies**
- Multi-site implementations
- Pragmatic evaluation designs
- Long-term follow-up
- Assessment across diverse patient populations
- Analysis of implementation factors

**4. Implementation Science**
- Study of adoption processes
- Identification of contextual factors
- Barriers and facilitators analysis
- Fidelity assessment
- Sustainability evaluation

---

## 4. Design Principles for Successful CDSS

### 4.1 The Five Rights Framework

The most widely recognized framework for effective CDSS design is the "Five Rights," developed by Osheroff and adopted by AHRQ and leading healthcare organizations.

**Framework:** Effective CDS delivers the **right information**, to the **right person**, in the **right format**, through the **right channel**, at the **right time** in workflow.

#### **1. Right Information**

**Characteristics:**
- Evidence-based, derived from recognized guidelines or performance measures
- Detailed enough to enable action
- Not so detailed as to cause information overload
- Actionable and specific to clinical context
- Current and regularly updated

**Considerations:**
- Strength of evidence supporting recommendation
- Relevance to specific patient population
- Clarity of action required
- Inclusion of supporting rationale

#### **2. Right Person**

**Approach:**
- Target whoever can take appropriate action
- May be physician, nurse, pharmacist, physical therapist, patient, or family member
- Exclude anyone who cannot take action
- Consider role-based distribution to reduce burden on physicians

**Evidence:**
- Shifting appropriate alerts to pharmacists or nurses improves efficiency
- Reduces physician alert burden
- Ensures clinical expertise matches intervention type

#### **3. Right Format**

**Options:**
- Alerts and reminders
- Order sets
- Clinical protocols and pathways
- Patient monitoring dashboards
- Information buttons
- Documentation templates
- Smart forms with embedded guidance

**Selection Criteria:**
- Best suited to solve the specific problem
- Matches urgency level (interruptive vs. non-interruptive)
- Aligns with user preferences and workflows
- Provides appropriate level of detail

**Evidence:**
- Standing orders generally more effective than reminders
- Non-interruptive formats reduce alert fatigue for non-critical information
- Order sets increase guideline adherence

#### **4. Right Channel**

**Channels:**
- EHR
- Computerized provider order entry (CPOE)
- Personal health record
- Mobile apps
- Smartphone notifications
- Even paper-based tools when appropriate

**Selection Factors:**
- Where user is working when decision needed
- Technical capabilities available
- User preferences and habits
- Integration with existing systems

#### **5. Right Time**

**Principles:**
- Deliver when user is making decision or taking action
- Just-in-time information delivery
- At natural decision points in workflow
- Not too early (will be forgotten) or too late (decision already made)

**Examples:**
- Medication alerts at prescribing time
- Preventive care reminders at visit documentation
- Diagnostic support during clinical assessment
- Risk scores at admission or transfer

**Evidence:**
- Providing decision support at time and location of care (vs. before) associated with success
- Poorly timed alerts contribute to fatigue and dismissal

### 4.2 The Four A's of User Interface Design

A complementary framework emphasizes four principles summarized as the "Four A's":

1. **All in One**: Integrate all necessary information and functions in single interface
2. **At a Glance**: Present information visually so key points immediately apparent
3. **At Hand**: Make CDS readily accessible with minimal navigation
4. **Attention**: Design to appropriately capture and direct user attention

**Integration Requirement:** Effective CDSS UI should integrate all four principles, not just one or two.

### 4.3 User-Centered Design Methodology

**Core Approach:**

Developers must adopt design practices including:
- User-centered, iterative design
- Common standards based on HCI research
- Methods rooted in ethnography and cognitive science
- Involvement of representative end-users throughout development
- Testing in realistic clinical contexts

**Process:**
1. Understand users, tasks, and context through observation and interviews
2. Define requirements with user input
3. Develop prototypes
4. Evaluate with users in realistic scenarios
5. Iterate based on feedback
6. Continue refinement post-deployment

**Evidence:**
- Limited consideration of CDS design best practices cited as key barrier to adoption
- Applying user-centered design principles critical for effectiveness
- Resource-intensive but essential investment

**Challenge:** Developing usable CDSS is difficult due to:
- Complex domain knowledge
- Complex context of use
- Need for significantly more research on mental models of clinical users

### 4.4 Minimize Cognitive Load and Workflow Disruption

**Principles:**

**1. Minimize Extra Clicks**
- Ideally, single click or zero clicks to access recommendation
- Auto-population of orders or notes when appropriate
- Streamlined acknowledgment or dismissal

**2. Reduce Task Switching**
- Interruptive alerts increase cognitive load via task switching
- Present information within current workflow context
- Avoid requiring switch to different application or screen

**3. Provide Appropriate Detail**
- Enough information to support decision
- Not so much as to cause information overload
- Layered information with summary and details on demand
- Visual presentation of key points

**4. Respect Expertise**
- Allow experts to bypass detailed guidance if desired
- Provide progressive disclosure
- Adapt to user experience level
- Avoid patronizing tone

### 4.5 Context-Awareness and Personalization

**Patient-Specific Recommendations:**

Effective CDSS must:
- Compare individual patient data to evidence-based guidelines
- Account for patient-specific factors (comorbidities, allergies, preferences)
- Integrate demographics, clinical history, and genomic information
- Tailor interventions to unique patient profile

**Contextual Adaptation:**

Systems should sense and react based on:
- Clinical environment (ED, ICU, outpatient)
- Urgency of situation
- Provider role and expertise
- Time of day and workload
- Patient status and trajectory

**Precision Medicine Integration:**
- Individual genetic and genomic factors
- Environmental exposures
- Lifestyle factors
- Social determinants of health

### 4.6 Explainability and Transparency

**Critical for AI/ML Systems:**

Given black box concerns, AI-based CDSS should:

**1. Provide Explanations**
- Clear statement of recommendation and rationale
- Supporting evidence and references
- Factors driving the recommendation
- Confidence level or uncertainty indication

**2. Use XAI Techniques When Needed**
- SHAP (SHapley Additive exPlanations) for feature importance
- LIME (Local Interpretable Model-agnostic Explanations)
- Attention mechanisms showing what model "looked at"
- Counterfactual explanations

**3. Consider Interpretability-Accuracy Trade-off**
- Simpler models (logistic regression, decision trees) more interpretable
- Complex models (deep neural networks) may be more accurate
- Choice should be context-dependent based on:
  - Clinical stakes
  - User needs
  - Regulatory requirements
  - Specific application

**4. Transparency About Limitations**
- Acknowledge what system can and cannot do
- Specify training data populations
- Identify known failure modes or biases
- Provide performance metrics

**Clinical Imperative:** In high-stakes medical decisions, clinicians must justify choices and ensure patient safety—opacity is unacceptable and undermines trust.

### 4.7 Governance and Continuous Improvement

**Governance Structures:**

Successful sites employ:
- Committees to govern development, implementation, and maintenance
- Clinical and technical representation
- Clear decision-making processes
- Regular review of CDS performance

**Continuous Monitoring:**
- Alert response rates
- Override patterns and reasons
- User feedback and complaints
- Clinical outcome metrics
- System performance and uptime
- Knowledge base currency

**Iterative Refinement:**
- Regular updates based on monitoring data
- A/B testing of alternative designs
- Sunset policies for ineffective interventions
- Scaling of successful interventions
- User training on improvements

---

## 5. Important Studies and Key Citations

### 5.1 Foundational Systematic Reviews

**Bright et al. (2012)** - "Effect of Clinical Decision-Support Systems: A Systematic Review"
- Landmark review showing CDSS can enhance clinical performance for drug dosing, preventive care
- 52% of studies measuring process of care showed improvement
- 31% measuring patient outcomes showed benefits
- Ann Intern Med. 2012;157(1):29-43

**Jaspers et al. (2011)** - "Effects of Clinical Decision-Support Systems on Practitioner Performance and Patient Outcomes: A Synthesis of High-Quality Systematic Review Findings"
- Meta-review synthesizing evidence across multiple systematic reviews
- Confirmed moderate evidence for practitioner performance improvement
- J Am Med Inform Assoc. 2011;18(3):327-334

**Moja et al. (2014)** - "Effectiveness of Computerized Decision Support Systems Linked to Electronic Health Records: A Systematic Review and Meta-Analysis"
- Focus on EHR-integrated CDSS
- Demonstrated importance of integration for effectiveness
- Am J Public Health. 2014;104(12):e12-22

### 5.2 Alert Fatigue and Mitigation

**Ancker et al. (2017)** - "Effects of Workload, Work Complexity, and Repeated Alerts on Alert Fatigue in a Clinical Decision Support System"
- Documented that reducing within-patient repeats promising for reducing fatigue
- Alert fatigue caused by uninformative alerts combined with complex work
- BMC Med Inform Decis Mak. 2017;17(1):36

**Nanji et al. (2019)** - "Medication Safety Alert Fatigue May Be Reduced via Interaction Design and Clinical Role Tailoring: A Systematic Review"
- Evidence that tiering alerts and role-based distribution effective
- Importance of interaction design highlighted
- J Am Med Inform Assoc. 2019;26(10):1141-1149

**McCoy et al. (2014)** - "A Framework for Evaluating the Appropriateness of Clinical Decision Support Alerts and Reminders"
- Clinicians averaged 56 alerts/day, 49 minutes processing
- Framework for assessing alert appropriateness
- Cogn Inform Cogn 2014

### 5.3 Medication Safety

**AHRQ Making Healthcare Safer IV (2024)** - "Computerized Clinical Decision Support To Prevent Medication Errors and Adverse Drug Events"
- Comprehensive evidence review
- Moderate evidence for reducing medication errors
- Low evidence for preventing ADEs
- Available at: NCBI Bookshelf NBK600580

**Raschke et al. (1998)** - "A Computer Alert System to Prevent Injury from Adverse Drug Events"
- Foundational study showing 44% of medication errors would be missed without CDS
- JAMA. 1998;280(15):1317-1320

### 5.4 AI/ML Clinical Decision Support

**Sendak et al. (2020)** - "Real-World Integration of a Sepsis Deep Learning Technology Into Routine Clinical Care: Implementation Study"
- Important real-world ML-CDSS deployment study
- JMIR Med Inform. 2020;8(7):e15182

**Adams et al. (2022)** - "Prospective, Multi-Site Study of Patient Outcomes After Implementation of the TREWS Machine Learning-Based Early Warning System for Sepsis"
- Multi-site ML sepsis prediction system
- Interaction with system associated with reduced mortality
- Nat Med. 2022;28(7):1455-1460

**Sutton et al. (2020)** - "An Overview of Clinical Decision Support Systems: Benefits, Risks, and Strategies for Success"
- Comprehensive review of CDSS including AI/ML approaches
- Discussion of black box problem and trust issues
- npj Digit Med. 2020;3:17

### 5.5 Interruptive vs. Non-Interruptive Interventions

**Poly et al. (2019)** - "Interruptive Versus Noninterruptive Clinical Decision Support: Usability Study"
- Direct comparison of interruptive and noninterruptive formats
- Trade-offs between workflow impact and visibility
- JMIR Hum Factors. 2019;6(2):e12469

**Beeler et al. (2019)** - "A Retrospective Analysis of Interruptive versus Non-interruptive Clinical Decision Support for Identification of Patients Needing Contact Isolation"
- Non-interruptive CDS users 7% less sensitive in identifying at-risk patients
- Demonstrates effectiveness trade-off
- AMIA Annu Symp Proc. 2013;2013:117-123

### 5.6 Implementation and Adoption

**Kilsdonk et al. (2017)** - "What Hinders the Uptake of Computerized Decision Support Systems in Hospitals? A Qualitative Study and Framework for Implementation"
- Identified 35 barriers and 25 facilitators to adoption
- Implementation framework development
- Implement Sci. 2017;12(1):113

**Kawamoto et al. (2005)** - "Improving Clinical Practice Using Clinical Decision Support Systems: A Systematic Review of Trials to Identify Features Critical to Success"
- Identified key features associated with CDSS success
- Integration into workflow as critical factor
- BMJ. 2005;330(7494):765

### 5.7 Choosing Wisely and Low-Value Care

**Cliff et al. (2021)** - "Reducing Routine Vitamin D Screening in Primary Care"
- Virginia Mason example of CDS reducing low-value testing
- Required explicit evidence-based rationale
- Dramatic reduction in inappropriate vitamin D screening
- JAMA Intern Med. 2021

### 5.8 Explainability and Trust

**Antoniadi et al. (2021)** - "Current Challenges and Future Opportunities for XAI in Machine Learning-Based Clinical Decision Support Systems: A Systematic Review"
- Comprehensive review of explainability challenges in AI-CDSS
- Discussion of XAI techniques (SHAP, LIME)
- Appl Sci. 2021;11(11):5088

**Kelly et al. (2019)** - "Key Challenges for Delivering Clinical Impact with Artificial Intelligence"
- Black box problem and clinical acceptance
- Trade-off between accuracy and interpretability
- BMC Med. 2019;17(1):195

### 5.9 User-Centered Design

**Horsky et al. (2012)** - "Interface Design Principles for Usable Decision Support: A Targeted Review of Best Practices for Clinical Prescribing Interventions"
- Best practices for CDS interface design
- Importance of user-centered approach
- Int J Med Inform. 2012;81(1):1-13

**Benda et al. (2011)** - "Four Principles for User Interface Design of Computerised Clinical Decision Support Systems"
- The Four A's framework (All in one, At a glance, At hand, Attention)
- Stud Health Technol Inform. 2011;169:65-69

### 5.10 Evaluation Frameworks

**Ash et al. (2012)** - "Recommended Practices for Computerized Clinical Decision Support and Knowledge Management in Community Settings: A Qualitative Study"
- Governance and best practices from leading institutions
- J Am Med Inform Assoc. 2012;19(1):146-152

**Talmon et al. (2009)** - "STARE-HI—Statement on Reporting of Evaluation Studies in Health Informatics"
- Standards for reporting health IT evaluation
- Int J Med Inform. 2009;78(1):1-9

---

## 6. Implications for Workflow-Sensitive AI Interventions to Reduce Low-Value Care

### 6.1 Critical Design Considerations

For organizations developing AI systems to reduce low-value care at the point of care, the CDSS literature provides crucial guidance:

#### **1. Prioritize Workflow Integration Above All Else**

**Evidence:**
- Integration into workflow (vs. separate logins/screens) most strongly associated with success
- Standalone systems that disrupt workflow face major adoption barriers
- Timing of intervention at natural decision points critical

**Implications:**
- AI interventions must be deeply embedded in existing EHR workflows
- Zero or single-click access to recommendations
- Auto-population of data to minimize clinician burden
- Delivery at moment of decision (e.g., during order entry for imaging/labs)
- No context switching or application hopping required

**For Low-Value Care Reduction:**
- Intervene at point of order entry for tests/procedures
- Provide alternative evidence-based options inline
- Make it easier to choose appropriate option than inappropriate one

#### **2. Reserve Interruptive Alerts for Truly Critical Situations**

**Evidence:**
- Interruptive alerts more effective but contribute heavily to alert fatigue
- Average 56 alerts/day causing 49 minutes of daily burden
- High override rates undermine all alerts including critical ones

**Implications:**
- For most low-value care interventions, use non-interruptive formats
- Consider "smart order sets" that make appropriate orders easier
- Use visual cues, templates, and defaults rather than pop-ups
- Reserve hard stops or interruptive alerts only for:
  - Immediate patient safety issues
  - High-cost, high-harm interventions
  - Clear contraindications

**Tiered Approach:**
- Severe/Critical: Interruptive with requirement for acknowledgment
- Moderate: Visual indicator with easy access to details
- Minor: Passive guidance via order organization, defaults, templates

#### **3. Implement Role-Based Distribution**

**Evidence:**
- Directing alerts to pharmacists or nurses (vs. physicians) effective
- 29% reduction in errors when appropriate alerts shifted to nurses
- Semi-automated review by clinical pharmacists reduces physician burden

**Implications:**
- Not all low-value care interventions need to go to ordering physician
- Consider:
  - Pre-authorization by utilization management
  - Clinical pharmacist review for medication-related concerns
  - Nursing team for care coordination alternatives
  - Patient outreach by care managers for unnecessary follow-up

**Benefit:** Reduces alert fatigue while ensuring clinical expertise reviews appropriateness

#### **4. Ensure Explainability and Provide Rationale**

**Evidence:**
- Black box AI recommendations face clinician mistrust
- Opacity undermines acceptance and raises liability concerns
- Clinicians must be able to justify decisions to patients and colleagues

**Implications:**
- Every AI recommendation must include:
  - Clear statement of concern (e.g., "This test rarely changes management for this indication")
  - Evidence-based rationale (guideline reference, literature citation)
  - Suggested alternative if appropriate
  - How patient-specific factors were considered
  - Confidence level or uncertainty

**For Complex ML Models:**
- Use XAI techniques (SHAP, LIME) to show influential factors
- Consider interpretable models for lower-stakes interventions
- Provide "why" explanation accessible via single click

**Build Trust:** Transparency about how system reached recommendation and acknowledgment of limitations

#### **5. Design for Appropriate Contextualization**

**Evidence:**
- Effective CDSS must provide patient-specific recommendations
- Generic, one-size-fits-all alerts frequently inappropriate
- Context-awareness improves relevance and reduces overrides

**Implications:**
- AI must account for:
  - Patient-specific clinical context (diagnosis, comorbidities, prior workup)
  - Urgency of situation (ED vs. routine outpatient)
  - Provider expertise and role
  - Prior testing and results
  - Goals of care and patient preferences

**For Low-Value Care:**
- Recognize when tests appropriate despite general low-value designation
- Avoid alerts when recent results available
- Consider clinical setting and acuity
- Account for diagnostic uncertainty appropriately

**Avoid:** One-size-fits-all rules that don't account for complexity leading to irrelevant alerts

#### **6. Support Shared Decision-Making, Don't Dictate**

**Evidence:**
- Alerts perceived as encroaching on autonomy generate resistance
- Professional identity threat from over-reliance on systems
- Mandatory compliance often counterproductive

**Implications:**
- Frame as decision support, not decision enforcement
- Provide information and alternatives to support informed choice
- Preserve physician final authority
- Avoid judgmental language ("inappropriate," "unnecessary")
- Use neutral framing: "Evidence suggests limited benefit for..." rather than "This order is not indicated"

**For Low-Value Care:**
- Educate about limited benefit and potential harms
- Offer evidence-based alternative approaches
- Support patient engagement in decision
- Allow override with brief rationale (track for QI, not punishment)

#### **7. Implement Robust Governance and Continuous Improvement**

**Evidence:**
- Successful sites have strong governance structures
- Regular monitoring of alert performance essential
- Knowledge base maintenance challenging even for advanced institutions
- After research support removed, practices often revert

**Implications:**
- Establish multidisciplinary governance committee (clinicians, IT, QI, admin)
- Regular review of:
  - Alert acceptance/override rates
  - Override reasons
  - Clinical outcomes
  - Unintended consequences
  - User feedback
- Systematic process for updating clinical logic
- A/B testing of alternative approaches
- Sunset policy for ineffective interventions

**For Long-term Success:**
- Plan for sustained funding and staffing beyond initial deployment
- Integration with organizational QI infrastructure
- Alignment with strategic priorities and incentives
- Executive sponsorship

#### **8. Measure What Matters**

**Evidence:**
- Many evaluations focus on system accuracy, not impact
- Need for comprehensive frameworks measuring net benefit
- Patient-centered outcomes often overlooked
- Process changes don't always translate to outcome improvements

**Implications:**
- Measure across four domains:
  1. **Process of care**: Order rates, guideline adherence, test utilization
  2. **Professional competency**: Clinician knowledge, decision quality
  3. **Patient outcomes**: Clinical outcomes, safety, patient experience
  4. **Cost-effectiveness**: Resource utilization, value

**For Low-Value Care Initiatives:**
- Primary: Reduction in targeted low-value services
- Secondary: Appropriate alternative care provided, patient outcomes, patient satisfaction, cost savings
- Balancing measures: Overall care quality, miss rates for appropriate care, clinician satisfaction
- Implementation: System usage, override rates, reasons for overrides

**Real-World Validation:** Prospective evaluation in actual clinical settings, not just retrospective accuracy

### 6.2 Specific Strategies for Low-Value Care Reduction

Based on successful CDSS implementations targeting overuse:

#### **1. Appropriateness Criteria at Order Entry**

**Virginia Mason Model:**
- Required providers to answer questions verifying appropriateness before imaging order
- Substantially decreased low-value lumbar MRI, head MRI, sinus CT
- Questions based on evidence-based appropriateness criteria

**Application:**
- Embed appropriateness criteria into order entry
- Ask structured questions about indication, prior workup, red flags
- Use responses to guide decision support
- Make appropriate orders easier than inappropriate ones

#### **2. Best Practice Advisories (BPAs) with Alternatives**

**Approach:**
- When low-value order attempted, trigger BPA explaining limited benefit
- Provide evidence-based alternative inline
- Single-click to switch to alternative
- Option to proceed with original with brief override reason

**Example for Vitamin D Screening:**
- Trigger when vitamin D ordered for screening (not diagnostic)
- Explain limited evidence for routine screening in asymptomatic patients
- Note costs and potential for cascading interventions
- Allow override for symptomatic patients or specific risk factors

#### **3. Smart Order Sets and Templates**

**Approach:**
- Default to evidence-based, high-value orders
- De-emphasize or require justification for low-value options
- Organize orders to guide appropriate decision-making

**Evidence:**
- Standing orders more effective than reminders
- Order organization shapes behavior
- Defaults have powerful influence

**Example:**
- Order set for low back pain includes:
  - First-line: Conservative management (PT, NSAIDs)
  - Clear criteria for when imaging appropriate
  - Imaging options de-emphasized unless criteria met

#### **4. Duplicate and Redundant Test Prevention**

**Hard Stop Approach:**
- Identify when recent result available
- Require justification to proceed with duplicate
- May require call to lab or supervisor approval for true duplicates

**Smart Alert Approach:**
- Notify of recent result and value
- Suggest using existing result
- Allow override if clinical change justifies repeat

**Evidence:**
- Both approaches effective at reducing duplicates
- Hard stops more effective but may frustrate for edge cases
- Smart alerts less disruptive but somewhat less effective

#### **5. Choosing Wisely Integration**

**Approach:**
- Systematically implement CDS for high-priority Choosing Wisely recommendations
- Target non-patient-facing interventions where clinician discretion high
- Examples: Duplicate labs, blood transfusion volumes, catheter duration, ICU antibiotics

**Success Factors:**
- Multi-stakeholder engagement
- Understanding local barriers
- Tailoring to specific clinical context
- Addressing both over-detection and over-treatment

### 6.3 Addressing the Challenge of AI/ML for Low-Value Care

The CDSS literature reveals important challenges when using AI/ML (vs. rules) for low-value care reduction:

#### **Challenges:**

**1. Explainability Critical**
- Clinicians unlikely to accept "black box" recommendations to not order test
- Need clear rationale they can explain to patients
- Liability concerns if harm results from following opaque AI recommendation

**2. Trust Lower for AI**
- Professional identity threat from AI questioning clinical judgment
- Concern about AI not understanding nuance of individual patient
- Fear of algorithmic bias

**3. Regulatory Uncertainty**
- Liability when following AI recommendations unclear
- FDA regulation evolving
- Local institutional policies may restrict AI in certain contexts

**4. Data Requirements**
- ML models need large, high-quality training datasets
- May not perform well on populations different from training data
- Risk of encoding biases from historical practice patterns

#### **When AI/ML May Add Value:**

**1. Complex Risk Prediction**
- When appropriateness depends on integration of many patient-specific factors
- Non-linear relationships
- Patterns not easily captured in simple rules
- Example: Predicting which patients with headache benefit from imaging based on symptom patterns, comorbidities, clinical trajectory

**2. Temporal Patterns**
- When decision should consider trajectory over time
- Example: Rate of change in labs suggesting need for intervention vs. stable chronic abnormality

**3. Unstructured Data Integration**
- When relevant information in clinical notes, imaging reports
- NLP to extract key information
- Example: Identifying patients with documented prior negative workup to avoid repeat testing

**4. Personalized Thresholds**
- When appropriate threshold varies by patient characteristics
- Example: When laboratory monitoring interval should be shortened based on individual risk factors

#### **Implementation Recommendations:**

**Start with Hybrid Approach:**
- Use ML for risk stratification or information extraction
- Apply rule-based logic for final recommendation
- Combines ML power with rule-based transparency

**Ensure Explainability:**
- Use interpretable features
- Provide feature importance (which factors drove prediction)
- Show similar cases and outcomes
- Indicate confidence/uncertainty

**Extensive Validation:**
- Prospective validation in target population
- Analysis of false positives and false negatives
- Testing across subpopulations for bias
- Ongoing monitoring post-deployment

**Transparent Limitations:**
- Acknowledge training data source and potential biases
- Specify populations where validated
- Identify known failure modes
- Provide performance metrics (sensitivity, specificity, PPV, NPV)

### 6.4 Learning from Failures

The literature documents common failure modes relevant to low-value care interventions:

#### **Failure Mode 1: "Crying Wolf" - Too Many Inappropriate Alerts**

**Problem:** Alert fatigue from high false positive rate leads to all alerts being ignored

**For Low-Value Care:**
- Inappropriateness criteria must have high specificity
- Better to miss some low-value care than trigger on many appropriate orders
- Pilot test and refine before broad deployment
- Monitor override rates—if >80%, intervention needs refinement

#### **Failure Mode 2: Not Addressing Root Cause**

**Problem:** Alert doesn't address why clinicians ordering low-value service

**Example:** If imaging ordered because:
- Patient expectation/demand → Alert won't help; need patient education, communication training
- Defensive medicine/liability concerns → Alert may worsen anxiety; need institutional protection
- Lack of alternative options → Need to provide accessible alternatives
- Convenience/workflow → Need to make appropriate option easier

**Solution:** Understand local barriers through qualitative research; design intervention to address root cause

#### **Failure Mode 3: One-Size-Fits-All Doesn't Fit Anyone**

**Problem:** Generic rules don't account for legitimate clinical variability

**Example:** "MRI not indicated for low back pain <6 weeks" misses patients with red flag symptoms

**Solution:**
- Sophisticated contextualization
- Exception handling built in
- Easy override when appropriate
- Learn from override patterns

#### **Failure Mode 4: Ignoring Unintended Consequences**

**Problem:** Reducing one type of low-value care may lead to different low-value care or harm

**Examples:**
- Restricting imaging may delay appropriate diagnosis
- Reducing lab testing may miss complications
- Eliminating one test may lead to ordering battery of other tests

**Solution:**
- Comprehensive evaluation including balancing measures
- Monitor for substitution effects
- Track patient outcomes, not just utilization
- Rapid-cycle refinement

#### **Failure Mode 5: Lack of Sustained Support**

**Problem:** After initial implementation enthusiasm wanes; system becomes outdated; practices revert

**Evidence:** When research-based support systems removed, clinicians returned to pre-study guideline adherence

**Solution:**
- Long-term funding and staffing
- Integration into operational infrastructure
- Executive sponsorship
- Regular governance review
- Alignment with institutional priorities and incentives
- Celebration of successes

---

## 7. Research Gaps and Future Directions

### 7.1 Critical Knowledge Gaps

Despite substantial research on CDSS, important gaps remain:

#### **1. ML-Based CDSS Real-World Effectiveness**

**Gap:**
- Most ML-CDSS research in controlled simulation settings
- Limited real-world deployment and validation
- Unclear how to achieve effectiveness at scale
- Mixed evidence on patient outcome improvements

**Needed:**
- Pragmatic trials of ML-CDSS in diverse real-world settings
- Multi-site implementations with rigorous evaluation
- Long-term sustainability studies
- Head-to-head comparisons of ML vs. rule-based approaches for specific applications
- Understanding of when ML adds value beyond simpler approaches

#### **2. Optimal Intervention Timing and Delivery**

**Gap:**
- Limited research on when in workflow to deliver interventions
- Insufficient understanding of how timing affects effectiveness
- Unclear how to balance "just in time" with "too interruptive"

**Needed:**
- Studies comparing different delivery timing for same intervention
- Research on cognitive load and task-switching effects
- Analysis of how urgency/acuity should modify delivery approach
- Investigation of ambient/passive information vs. active recommendations

#### **3. Explainability Requirements and Methods**

**Gap:**
- Unclear how much explainability needed for different applications
- Limited evidence on which XAI techniques most effective for clinicians
- Insufficient research on explainability-accuracy trade-off in clinical context

**Needed:**
- User research on clinician explainability needs by context
- Comparative studies of XAI approaches (SHAP, LIME, attention, etc.)
- Research on when interpretable models sufficient vs. complex models with explanations needed
- Standards for adequate explanation in clinical AI

#### **4. Effective Strategies for Reducing Low-Value Care**

**Gap:**
- Limited evidence on which CDSS approaches most effective for low-value care reduction
- Insufficient understanding of mechanisms (behavior change, decision support, system redesign)
- Unclear how to achieve sustained reductions vs. short-term effects
- Little research on unintended consequences

**Needed:**
- Comparative effectiveness research on different de-implementation strategies
- Studies of interventions targeting Choosing Wisely recommendations
- Research on root causes of low-value ordering and how to address
- Long-term follow-up of low-value care interventions
- Analysis of balancing measures and potential harms

#### **5. Optimal Alert Volume and Prioritization**

**Gap:**
- No clear guidelines on maximum acceptable alerts per clinician
- Limited evidence on how to prioritize when multiple alerts triggered
- Insufficient research on cumulative burden across all CDS interventions

**Needed:**
- Studies establishing cognitive load limits for alerts
- Research on alert prioritization algorithms
- Investigation of cross-system alert coordination
- Development of "alert budgets" or governance frameworks

#### **6. Role of Patient-Facing CDS**

**Gap:**
- Most CDSS research focuses on clinician-facing tools
- Limited evidence on patient-facing decision support for low-value care
- Unclear how to engage patients in reducing unnecessary care

**Needed:**
- Research on patient education interventions embedded in clinical workflow
- Studies of shared decision-making tools for low-value care
- Investigation of patient portals and personal health records for CDS delivery
- Analysis of patient-clinician communication when CDS suggests less care

#### **7. Implementation Science**

**Gap:**
- Limited understanding of contextual factors affecting success
- Insufficient frameworks for assessing implementation readiness
- Unclear how to adapt CDSS across different settings
- Need better understanding of sustainability factors

**Needed:**
- Multi-site implementation studies using implementation science frameworks
- Research on organizational factors predicting success
- Development of implementation toolkits and best practices
- Studies of long-term sustainability beyond research funding

#### **8. Health Equity and Bias**

**Gap:**
- Limited research on how CDSS affect health disparities
- Insufficient attention to algorithmic bias in clinical AI
- Unclear how to ensure equitable access to benefits of CDSS
- Need better understanding of potential for AI to exacerbate or reduce disparities

**Needed:**
- Evaluation of CDSS performance across patient subgroups
- Research on bias detection and mitigation in clinical AI
- Studies of CDSS impact on disparities in care
- Development of equity-focused design and evaluation frameworks

#### **9. Cost-Effectiveness**

**Gap:**
- Limited high-quality cost-effectiveness analyses of CDSS
- Unclear return on investment for different types of interventions
- Insufficient understanding of development and maintenance costs

**Needed:**
- Rigorous cost-effectiveness analyses including:
  - Development costs
  - Implementation costs
  - Ongoing maintenance
  - Clinician time
  - Benefits (improved outcomes, reduced low-value care, efficiency)
- Comparison of different CDSS approaches
- Analysis of factors affecting ROI

#### **10. Comprehensive Evaluation Frameworks**

**Gap:**
- Evaluation often focuses on system accuracy or process measures
- Insufficient attention to end-user performance and patient outcomes
- Lack of standard metrics for comparing across studies
- Need for frameworks integrating technology, behavior, and outcomes

**Needed:**
- Consensus on core outcome measures for CDSS evaluation
- Standardized reporting guidelines
- Frameworks that assess:
  - System technical performance
  - Usability and user experience
  - Behavioral impacts (adoption, usage patterns)
  - Process outcomes
  - Clinical outcomes
  - Patient-centered outcomes
  - Cost-effectiveness
  - Implementation factors
  - Sustainability

### 7.2 Methodological Advances Needed

**1. Better Study Designs**
- More randomized controlled trials of CDSS interventions
- Pragmatic trials in real-world settings
- Stepped-wedge designs for system-level interventions
- N-of-1 trials for personalized decision support

**2. Advanced Analytics**
- Causal inference methods to understand mechanisms
- Machine learning for identifying optimal intervention targets
- Natural language processing for analyzing override reasons and user feedback
- Time-series analyses for temporal effects

**3. Mixed Methods**
- Integration of quantitative outcomes with qualitative understanding
- Ethnographic studies of CDSS use in practice
- Participatory design research
- Implementation science approaches

**4. Continuous Learning Systems**
- CDSS that adapt based on local usage patterns
- Reinforcement learning for intervention optimization
- Rapid-cycle improvement methods
- Real-time feedback loops

### 7.3 Future Directions

#### **Emerging Technologies**

**Large Language Models (LLMs):**
- Potential for natural language interaction with CDSS
- Enhanced NLP for extracting clinical information
- Automated generation of explanations
- Conversational interfaces for complex decision support

**Ambient Computing:**
- Voice-activated clinical decision support
- Reduced need for manual data entry
- More natural integration into workflow
- Potential for reducing documentation burden while improving CDS

**Federated Learning:**
- Learning from distributed data without centralization
- Privacy-preserving ML model development
- Ability to learn from multi-institutional data while maintaining local control

**Digital Twins:**
- Simulation of patient trajectories
- Personalized prediction of intervention effects
- What-if analysis for treatment decisions

#### **Evolving Paradigms**

**From Reactive to Proactive:**
- Shift from alerting to prediction and prevention
- Anticipatory guidance before problems arise
- Population health management integrated with individual care

**From Clinician-Centric to Team-Based:**
- CDS for entire care team, not just physicians
- Role-based distribution as standard practice
- Patient as active participant in CDS loop

**From Standalone to Integrated:**
- CDS as core EHR functionality, not add-on
- Interoperable CDS across systems
- Standards-based sharing of CDS knowledge

**From One-Size-Fits-All to Precision:**
- Highly personalized recommendations
- Integration of genomic and multi-omic data
- Adaptation to individual patient preferences and values
- Recognition of social determinants of health

**From Static to Continuously Learning:**
- Systems that improve with use
- Real-world evidence generation as part of care delivery
- Rapid incorporation of new evidence
- Local adaptation and optimization

---

## 8. Conclusion and Recommendations

### 8.1 Summary of Evidence

The literature on Clinical Decision Support Systems provides a substantial evidence base with important lessons for developing AI interventions to reduce low-value care:

**What We Know Works:**
- Integration into clinical workflow (not standalone systems)
- Delivery at point of care and moment of decision
- Patient-specific, contextualized recommendations
- Clear, actionable guidance with supporting rationale
- User-centered design with clinician involvement
- Strong governance and continuous improvement
- Role-based distribution to reduce physician burden
- Tiered alerts reserving interruption for critical situations

**What Doesn't Work:**
- High volume of poorly targeted alerts
- One-size-fits-all recommendations without context
- "Black box" systems without explanation
- Standalone applications disrupting workflow
- Mandatory compliance without clinical override
- Static systems without ongoing maintenance
- Implementation without adequate clinician training and buy-in

**What Remains Uncertain:**
- Optimal balance of interruptive vs. non-interruptive for different situations
- When ML adds sufficient value over rules to justify complexity
- How much explainability required for different applications
- Effectiveness of AI-based CDSS at reducing low-value care at scale
- Long-term sustainability of CDSS interventions
- Impact on health equity and disparities

### 8.2 Recommendations for Building AI Systems to Reduce Low-Value Care

Based on this comprehensive review, organizations developing AI interventions to reduce low-value care at the point of care should:

#### **1. Design Principles**

**Prioritize:**
- Deep workflow integration over powerful but separate tools
- Explainability and transparency over marginal accuracy gains
- User-centered design over technology-driven development
- Simplicity and usability over feature completeness
- Continuous improvement over "set and forget"

**Apply the Five Rights Framework:**
- Right Information: Evidence-based, actionable, appropriately detailed
- Right Person: Role-based distribution, not just physicians
- Right Format: Match urgency to format (mostly non-interruptive for low-value care)
- Right Channel: Embedded in EHR workflow
- Right Time: At moment of decision

#### **2. Implementation Approach**

**Start Small and Learn:**
- Pilot with single high-impact, low-complexity intervention
- Extensive user testing and iteration
- Measure comprehensively (process, outcomes, user experience)
- Refine based on data before scaling

**Build Governance:**
- Multidisciplinary committee (clinical, IT, QI, administration)
- Clear decision-making processes
- Regular review of performance data
- Systematic update processes for clinical knowledge

**Engage Stakeholders:**
- Involve end-users from beginning
- Address concerns about autonomy and professional identity
- Share performance data and successes
- Provide training and ongoing support

**Plan for Sustainability:**
- Long-term funding beyond initial implementation
- Integration into operational infrastructure
- Alignment with institutional incentives
- Executive sponsorship

#### **3. Technical Considerations**

**When to Use AI/ML vs. Rules:**
- **Use Rules When:**
  - Evidence-based guidelines clear and comprehensive
  - Explainability critical and simple rationale needed
  - Training data insufficient
  - Edge cases and errors unacceptable

- **Consider ML When:**
  - Many patient-specific factors with complex interactions
  - Temporal patterns or trajectories important
  - Need to extract information from unstructured data
  - Simple rules performing poorly
  - Large, high-quality training data available

**If Using ML:**
- Ensure explainability through XAI techniques or interpretable models
- Extensive validation across patient subpopulations
- Monitoring for bias and equity impacts
- Transparent performance metrics
- Consider hybrid approaches (ML + rules)

**For All Systems:**
- Standards-based development (FHIR, CDS Hooks)
- Interoperability with EHR systems
- Robust data quality processes
- Security and privacy protections

#### **4. Evaluation Strategy**

**Measure Comprehensively:**
- **Process:** Intervention usage, override rates, order patterns
- **Professional:** Clinician satisfaction, trust, workflow impact
- **Patient:** Clinical outcomes, safety, satisfaction, equity
- **Economic:** Resource utilization, cost savings, ROI

**Include Balancing Measures:**
- Monitor for unintended consequences
- Track appropriate care not being reduced
- Assess substitution effects
- Evaluate impact on disparities

**Use Rapid Cycles:**
- Frequent data review (weekly/monthly, not just annual)
- Quick refinements based on findings
- A/B testing of alternatives
- Responsive to user feedback

#### **5. Cultural and Organizational Factors**

**Build Trust:**
- Transparency about system logic and performance
- Acknowledge limitations and uncertainties
- Frame as support for clinical judgment, not replacement
- Provide override option with easy documentation
- Share successes and lessons learned

**Address Barriers:**
- Understand root causes of low-value ordering through qualitative research
- Design interventions to address causes (not just symptoms)
- Provide alternatives when recommending against orders
- Support patient-clinician communication about less care
- Align incentives and reduce liability concerns where possible

**Promote Learning Culture:**
- View CDSS as continuous improvement tool
- Share data transparently
- Celebrate successes
- Learn from failures without blame
- Engage frontline clinicians as partners

### 8.3 Final Thoughts

Clinical Decision Support Systems, enhanced by AI and machine learning, hold tremendous promise for improving healthcare quality and reducing low-value care. However, realizing this promise requires learning from decades of CDSS research demonstrating both successes and failures.

The most sophisticated AI is worthless if clinicians don't use it or trust it. The most evidence-based recommendation is ineffective if it interrupts workflow or appears at the wrong time. The most accurate prediction is dangerous if it cannot be explained or if it encodes bias.

Success requires:
- Relentless focus on user needs and workflow integration
- Appropriate use of technology (simple when possible, complex when necessary)
- Transparency and explainability to build trust
- Comprehensive evaluation including unintended consequences
- Sustained organizational commitment and governance
- Continuous learning and improvement

For organizations developing AI interventions to reduce low-value care, the path forward is clear: start with user needs, design for workflow integration, ensure explainability, measure comprehensively, and commit to continuous improvement. The evidence base provides a strong foundation—but success will require translating these principles into practice with careful attention to local context, user experience, and sustained organizational support.

The opportunity is substantial: reducing the estimated 30% of healthcare spending on unnecessary, wasteful, or harmful care while improving patient outcomes and clinician satisfaction. Achieving this opportunity requires building on the lessons learned from CDSS research and implementation over the past decades—learning from both successes and failures to create interventions that are effective, sustainable, and trusted by clinicians and patients alike.

---

## References and Key Resources

### Major Systematic Reviews and Meta-Analyses

1. AHRQ Making Healthcare Safer IV. (2024). Computerized Clinical Decision Support To Prevent Medication Errors and Adverse Drug Events. NCBI Bookshelf NBK600580.

2. Bright, T. J., et al. (2012). Effect of clinical decision-support systems: a systematic review. Annals of Internal Medicine, 157(1), 29-43.

3. Sutton, R. T., et al. (2020). An overview of clinical decision support systems: benefits, risks, and strategies for success. npj Digital Medicine, 3, 17.

4. Moja, L., et al. (2014). Effectiveness of computerized decision support systems linked to electronic health records: a systematic review and meta-analysis. American Journal of Public Health, 104(12), e12-22.

5. Jaspers, M. W., et al. (2011). Effects of clinical decision-support systems on practitioner performance and patient outcomes: a synthesis of high-quality systematic review findings. Journal of the American Medical Informatics Association, 18(3), 327-334.

### Alert Fatigue and Mitigation

6. Ancker, J. S., et al. (2017). Effects of workload, work complexity, and repeated alerts on alert fatigue in a clinical decision support system. BMC Medical Informatics and Decision Making, 17(1), 36.

7. Nanji, K. C., et al. (2019). Medication safety alert fatigue may be reduced via interaction design and clinical role tailoring: a systematic review. Journal of the American Medical Informatics Association, 26(10), 1141-1149.

### AI/ML Clinical Decision Support

8. Adams, R., et al. (2022). Prospective, multi-site study of patient outcomes after implementation of the TREWS machine learning-based early warning system for sepsis. Nature Medicine, 28(7), 1455-1460.

9. Sendak, M. P., et al. (2020). Real-world integration of a sepsis deep learning technology into routine clinical care: implementation study. JMIR Medical Informatics, 8(7), e15182.

10. Kelly, C. J., et al. (2019). Key challenges for delivering clinical impact with artificial intelligence. BMC Medicine, 17(1), 195.

### Explainability and Trust

11. Antoniadi, A. M., et al. (2021). Current challenges and future opportunities for XAI in machine learning-based clinical decision support systems: a systematic review. Applied Sciences, 11(11), 5088.

### Design and Implementation

12. Kawamoto, K., et al. (2005). Improving clinical practice using clinical decision support systems: a systematic review of trials to identify features critical to success. BMJ, 330(7494), 765.

13. Horsky, J., et al. (2012). Interface design principles for usable decision support: a targeted review of best practices for clinical prescribing interventions. International Journal of Medical Informatics, 81(1), 1-13.

14. Benda, N. C., et al. (2011). Four principles for user interface design of computerised clinical decision support systems. Studies in Health Technology and Informatics, 169, 65-69.

### Implementation and Adoption

15. Kilsdonk, E., et al. (2017). What hinders the uptake of computerized decision support systems in hospitals? A qualitative study and framework for implementation. Implementation Science, 12(1), 113.

16. Ash, J. S., et al. (2012). Recommended practices for computerized clinical decision support and knowledge management in community settings: a qualitative study. Journal of the American Medical Informatics Association, 19(1), 146-152.

### Key Framework and Methods Papers

17. Osheroff, J. A., et al. (2012). Improving Outcomes with Clinical Decision Support: An Implementer's Guide, Second Edition. HIMSS.

18. Talmon, J., et al. (2009). STARE-HI—Statement on reporting of evaluation studies in health informatics. International Journal of Medical Informatics, 78(1), 1-9.

---

**Document prepared for:** PSALMS AI Analysis Project
**Focus:** Reducing low-value care through AI-powered interventions at the point of care
**Next steps:** Application of these principles to specific use cases and intervention design
