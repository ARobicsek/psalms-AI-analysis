# Literature Review: Low-Value Care & De-Implementation Science

**Document Type:** Foundational Literature Review
**Date Created:** November 17, 2025
**Primary Focus:** Evidence base for AI-assisted interventions to reduce low-value care at the point of care
**Literature Source:** PubMed-indexed peer-reviewed publications

---

## Executive Summary

Low-value care—healthcare services that provide little or no benefit to patients, potentially cause harm, or waste resources—represents a major challenge in modern healthcare, accounting for an estimated **25% of total healthcare spending** ($760-935 billion annually in the US alone). De-implementation science, the systematic study of removing ineffective or harmful practices, has emerged as a critical field for addressing this problem.

### Key Findings:

1. **Magnitude of the Problem**: Physicians estimate that ~20% of medical care is unnecessary, including 22% of medications, 25% of tests, and 11% of procedures. Common areas of overuse include diagnostic imaging, preoperative testing, antibiotic prescribing, proton pump inhibitors, and cancer screening.

2. **Drivers of Overuse**: Fear of malpractice (85% of physicians cite this), patient pressure (59%), difficulty accessing records (38%), financial incentives, expanding disease definitions, and defensive medicine practices drive overuse.

3. **What Works**: Multicomponent interventions targeting both patients and clinicians are most effective. Active implementation strategies (clinical decision support, audit and feedback, order set optimization) significantly outperform passive dissemination alone (65% vs 13% success rate). Behavioral economics-informed interventions show promise, with one RCT reducing low-value care from 20.5% to 16.0%.

4. **Critical Barriers**: Lack of credible evidence (21%), entrenched norms and resistance to change (21%), patient demands (6%), lack of time, fear of errors, and organizational context challenges impede de-implementation efforts.

5. **Implementation Science**: 27 unique frameworks exist for de-implementation, with 50% of ERIC implementation strategies mapped to de-implementation purposes. Most effective strategies involve changing infrastructure/workflow and developing stakeholder relationships.

6. **Measurement Challenges**: 26 claims-based measures exist for Medicare, covering cancer screening, diagnostic testing, preoperative testing, imaging, cardiovascular procedures, and surgical procedures. However, measurement approaches vary widely.

### Implications for AI-Assisted Point-of-Care Interventions:

AI systems have unique potential to address low-value care through:
- **Real-time clinical decision support** optimized to reduce alert fatigue
- **Predictive analytics** to identify high-risk scenarios for overuse
- **Behavioral economics integration** through default settings and nudges
- **Evidence delivery** at the moment of decision-making
- **Audit and feedback automation** with actionable recommendations

However, AI implementation must carefully address alert fatigue (33-96% of alerts are ignored), ensure equity, avoid contributing to overuse, and integrate with clinical workflows.

---

## 1. Key Definitions and Concepts

### 1.1 Low-Value Care

**Definition**: Healthcare services that provide little or no benefit to patients relative to their harms and costs, including services where evidence suggests they are ineffective, harmful, or of uncertain benefit compared to alternatives.

**Scope**: Low-value care encompasses:
- Unnecessary diagnostic tests and imaging
- Inappropriate medications (wrong indication, duration, or dose)
- Ineffective procedures and surgeries
- Overtreatment of conditions unlikely to cause harm
- Preventive services in low-risk populations

### 1.2 Medical Overuse and Overtreatment

**Medical Overuse**: The provision of healthcare services for which the potential for harm exceeds the potential for benefit (PMID: 28877170).

**Key Statistics** (PMID: 31498374, 27654002):
- Physicians report median of **20.6% of overall medical care is unnecessary**
- 22.0% of prescription medications unnecessary
- 24.9% of tests unnecessary
- 11.1% of procedures unnecessary

**Common Patterns of Overtreatment**:
- 39% of urgent care clinic visits result in antibiotic prescriptions
- 94% of testosterone replacement therapy administered off-guideline
- 61% of diabetic patients treated to potentially harmful HbA1c levels
- 25% of low-risk atrial fibrillation patients receive anticoagulation
- Up to 30% of healthcare costs attributed to overtreatment

**Causes** (PMID: 28877170, 33717342):
- Fear of malpractice (84.7%)
- Patient pressure/requests (59.0%)
- Difficulty accessing medical records (38.2%)
- Financial incentives favoring volume over value
- Expanding disease definitions
- Pharmaceutical industry influence
- Defensive medicine practices
- Physician training emphasizing action over restraint

### 1.3 Overdiagnosis

**Definition**: Detection of conditions that, if left undetected, would not cause symptoms or early death (PMID: 28765855, 20413742).

**Magnitude**:
- ~25% of mammographically detected breast cancers
- ~50% of chest x-ray/sputum-detected lung cancers
- ~60% of PSA-detected prostate cancers
- 18.5% of LDCT-detected lung cancers in NLST
- >70% of thyroid cancers in China

**Harms** (PMID: 30298054):
- Overtreatment with associated toxicities
- Diagnosis-related anxiety and depression
- Patient labeling effects
- Financial burden
- Cascade effects leading to additional unnecessary testing/treatment

### 1.4 Cascade Effects

**Definition**: A chain of events initiated by an unnecessary test or procedure that leads to additional interventions, each carrying risks of harm.

**Evidence** (PMID: 26568269, 35177360):
- Low-value thyroid testing can trigger cascades of overdiagnosis and overtreatment
- Emergency department overtesting commonly leads to downstream consequences
- Marginal test results and their cascades accumulate significant costs and harms
- Importance of both preventing low-value tests initially and mitigating cascades when they arise

### 1.5 De-Implementation Science

**Definition**: The scientific study of processes for reducing or ceasing the use of health practices that are ineffective, unproven, low-value, or harmful (PMID: 29225448).

**Framework** (PMID: 34819122):
- Identifies problem areas of low-value and wasteful practice
- Conducts rigorous examination of factors initiating and maintaining such behaviors
- Employs evidence-based interventions to cease these practices
- Represents a "virtuous cycle" of stopping low-value care before implementing new high-value care

**Scope** (PMID: 36303219):
- 27 unique frameworks and models identified
- 50% of ERIC implementation strategies applicable to de-implementation
- 5 unique de-implementation-specific strategies identified
- Studied across broad array of disciplines beyond healthcare

### 1.6 Therapeutic Inertia vs. Clinical Inertia

**Clinical Inertia** (PMID: 11694107):
Original definition: Failure of healthcare providers to initiate or intensify therapy when indicated.

**Three Core Problems**:
1. Overestimation of care provided
2. Use of "soft" reasons to avoid treatment intensification
3. Lack of education, training, and practice organization for achieving therapeutic goals

**Therapeutic Inertia** (PMID: 38444892, 24989986):
More specific term: Failure to initiate or intensify therapy when therapeutic goals are not reached.

**Prevalence Across Conditions**:
- Type 2 diabetes (most studied—"a challenge that just won't go away")
- Hypertension
- Heart failure with reduced ejection fraction
- Psoriatic arthritis
- Multiple sclerosis

**Critical Distinction**: While clinical inertia represents underuse/undertreatment (failure to act when action is needed), it contrasts with overuse/overtreatment (acting when restraint is warranted). Both represent failures to deliver appropriate, evidence-based care.

---

## 2. The Choosing Wisely Campaign

### 2.1 Overview and Effectiveness

**The Initiative**: Multi-society campaign to reduce unnecessary medical tests, treatments, and procedures through physician-patient dialogue.

### 2.2 Key Evidence

**Systematic Review** (PMID: 34402553):
- **Major Finding**: Dissemination of Choosing Wisely guidelines alone is unlikely to reduce low-value service use
- **Active vs. Passive**: Active interventions achieved intended results 65% vs 13% for passive dissemination (p < 0.001)
- **Multicomponent Advantage**: Interventions with multiple components more successful than single-component (77% vs 47%, p = 0.002)
- **Target Matters**: More effective when targeting clinicians rather than patients
- **Best Approach**: Multicomponent interventions built on CW recommendations can effectively change practice patterns

**Population-Level Impact** (PMID: 26457643):
- Analyzed 7 low-value services nationally
- Modest decreases in 2 recommendations:
  - Imaging for headache
  - Cardiac imaging for low-risk patients
- Effect sizes marginal, suggesting need for additional interventions beyond awareness

**Physician Awareness** (PMID: 29137515):
- **Sobering Finding**: No significant change in awareness 2014-2017
- 21% aware in 2014 → 25% in 2017 (not significant)
- Despite continued publicity and physician outreach
- Among aware physicians, campaign valued and utilized

**Specialty-Specific: Oncology** (PMID: 35930757):
- 98 articles addressing 32 unique recommendations
- Most reported passive changes in adherence post-publication
- Limited uptake observed
- **Conclusion**: More attention needed for active implementation support

**Specialty-Specific: Surgery** (PMID: 32492121):
- Systematic review of de-implementation for low-value breast cancer surgery
- Variable success across different procedures
- Need for tailored implementation strategies

**Success Story: Canada** (PMID: 31722930):
- Choosing Wisely Canada campaign reduced TSH testing in primary care
- Demonstrates effectiveness when actively implemented
- Retrospective parallel cohort design

### 2.3 Evidence Quality

**Appraisal Study** (PMID: 29694449):
- Assessed evidence supporting Choosing Wisely® recommendations
- Findings highlight need for stronger evidence base
- Variable quality across recommendations

### 2.4 Measurement Framework

**Framework Development** (PMID: 26092165):
Integrated framework to assess campaign impact on low-value care including:
- Process measures (awareness, adoption)
- Outcome measures (utilization changes)
- Contextual factors
- Temporal considerations

---

## 3. De-Implementation Strategies and Frameworks

### 3.1 Frameworks and Models

**Scoping Review of Frameworks** (PMID: 34819122):
- **27 unique frameworks and models** identified from 27 articles
- Most applicable to **two or more levels** of Socio-Ecological Framework
- **Organization level** most commonly assessed
- De-implementation studied across broad disciplines
- **Gap**: Limited integration of learnings from other fields into implementation science

**Updated CFIR** (PMID: 36309746):
- Consolidated Framework for Implementation Research updated based on user feedback
- Widely used in implementation science
- Applicable to both implementation and de-implementation

**Combined CFIR and TDF Use** (PMID: 28057049):
- Systematic review of combined framework application
- CFIR: Comprehensive set of implementation determinants
- TDF: Intervention development focused
- Complementary purposes justify using both together

**TDF Application Guide** (PMID: 28637486):
Benefits of using Theoretical Domains Framework:
- Provides theoretical basis for implementation studies
- Good coverage of reasons for slow evidence diffusion
- Method for progressing from theory-based investigation to intervention

**Surgery-Specific Framework** (PMID: 32740238):
- Tailored framework for de-implementation in surgery
- Addresses unique surgical context factors

### 3.2 Implementation Strategies

**Scoping Review of Strategies** (PMID: 36303219):
- **50% of ERIC implementation strategies** used for de-implementation
- 62 strategies mapped onto ERIC taxonomy
- **5 de-implementation-specific strategies** identified that couldn't be mapped
- **Most Promising Clusters**:
  1. Change infrastructure and workflow
  2. Develop stakeholder interrelationships

**Analysis of 121 Randomized Trials** (PMID: 37428942):
- Most deimplementation strategies achieved **considerable reduction** of low-value care
- **No evidence** that particular type or number of interventions works best
- Suggests flexibility in strategy selection based on context

**Effectiveness Overview** (PMID: 39103927):
Systematic review of systematic reviews (2024):
- **Effective for**: Reducing medication usage (especially antibiotics and opioids)
- **Inconsistent for**: Low-value laboratory tests and imaging
- Mixed results suggest need for tailored approaches by service type

### 3.3 Multicomponent Interventions

**Systematic Review** (PMID: 27402662):
**Key Conclusion**: Multicomponent interventions addressing both patient and clinician roles have **greatest potential** to reduce low-value care.

**Evidence-Based Strategies**:
- Clinical decision support: Solid evidence base
- Performance feedback: Promising with good evidence
- Financial incentives: Mixed results
- Educational interventions: Insufficient alone

**Components Often Combined**:
1. Clinical decision support tools
2. Audit and feedback
3. Educational interventions
4. Provider engagement
5. Patient education materials
6. System-level changes (e.g., order set modifications)

### 3.4 Specific Strategy Evidence

**Clinical Decision Support**:
- Detailed in Section 7 (CDS and Technology)

**Audit and Feedback**:
- Detailed in Section 8 (Audit and Feedback)

**Behavioral Economics**:
- Detailed in Section 9 (Behavioral Economics)

**Order Set Optimization**:
- Detailed in Section 10 (Order Sets and CPOE)

---

## 4. Barriers and Facilitators to Reducing Low-Value Care

### 4.1 Comprehensive Evidence Synthesis

**Qualitative Evidence Synthesis** (PMID: 33127636):
Systematic review identifying barriers and facilitators across **five categories**:

**1. Individual Provider Factors** (74% barriers):
- Knowledge gaps about evidence
- Attitudes toward guidelines
- Clinical skills and experience
- Fear of missing diagnoses
- Professional autonomy concerns

**2. Individual Patient Factors** (72% barriers):
- Patient expectations and demands
- Health literacy levels
- Previous healthcare experiences
- Anxiety about undertreatment

**3. Social Context** (41% barriers, 48% facilitators):
- Peer influences and social norms
- Patient-provider relationship quality
- Communication patterns
- Professional culture

**4. Organizational Context** (67% barriers):
- Resource availability
- Staffing levels
- Time constraints
- EHR capabilities
- Quality metrics and incentives

**5. Economic/Political Context** (71% barriers):
- Financial incentives favoring volume
- Fee-for-service payment models
- Malpractice liability concerns
- Regulatory requirements

### 4.2 Recent Empirical Studies

**Healthcare Personnel Perceptions Review** (PMID: 39659728):
- **Knowledge** and **environmental context/resources**: Most common influence factors (n=16 each)
- **Education**: Most discussed intervention strategy (n=14)
- Highlights need for both knowledge provision and system support

**Primary Care Physicians Survey** (PMID: 38724909):
- **>80%** consider overtreatment/overdiagnosis a problem nationally
- **~50%** acknowledge problem in their own practice (perception gap)
- **Common Barriers**:
  - Lack of time
  - Fear of error
  - Patient pressures
  - Medicolegal concerns

**Low Back Pain Study - Iran** (PMID: 38233835):
Qualitative multi-professional study identified:
- Cultural expectations for intervention
- Limited guideline awareness
- Financial pressures
- Inadequate interprofessional communication

**Home-Based Nursing Care** (PMID: 39171676):
**Facilitators**:
- Enhancing knowledge and skills
- Cross-professional collaboration
- Involving relatives in care
- Motivating client self-care
- Organizational support

**Barriers**:
- Non-reimbursement for evidence-based approaches
- Additional costs of care aids
- Client/relative resistance behaviors

**ICU Settings** (PMID: 30878979):
Multi-method study in Canadian ICUs:
- High variation in practice patterns
- Professional autonomy valued highly
- Need for multidisciplinary buy-in
- Importance of local champions

### 4.3 Multi-Method De-Implementation Study

**Comprehensive Analysis** (PMID: 35387673):
From 172 articles, identified **29 distinct barriers** and **24 distinct facilitators**.

**Most Common Barriers**:
1. Lack of credible evidence (21%)
2. Entrenched norms and resistance to change (21%)
3. Concerns about patient safety
4. Patient demands and expectations (6%)
5. Financial disincentives for reducing services

**Most Common Facilitators**:
1. Stakeholder collaboration and communication (15%)
2. Availability of credible evidence (12%)
3. Leadership support
4. Multidisciplinary engagement
5. Aligned financial incentives

### 4.4 Cross-Cutting Themes

**The "Iron Triangle" of Barriers**:
1. **Medicolegal Concerns**: Fear of malpractice drives defensive medicine
2. **Patient Expectations**: Perceived demand for "something to be done"
3. **Financial Incentives**: Volume-based payment rewards more services

**Facilitator Themes**:
1. **Evidence Credibility**: Trusted, high-quality evidence from respected sources
2. **Collaboration**: Engaging all stakeholders in co-design
3. **System Support**: Organizational infrastructure enabling change
4. **Measurement**: Transparent data on current practice patterns

---

## 5. Measurement Approaches and Metrics

### 5.1 Frameworks for Measurement

**Framework for Measuring Low-Value Care** (PMID: 29680091):
Integrated framework combining multiple methods to:
- Estimate magnitude of low-value care nationwide
- Track trends over time
- Identify principal sources of clinical waste
- Enable cross-system comparisons

**Measurement Challenges**:
- Defining what constitutes "low-value" (context-dependent)
- Data availability and quality
- Attribution issues
- Distinguishing appropriate from inappropriate use

### 5.2 Claims-Based Measures

**Medicare Measures** (PMID: 24819824):
Developed **26 claims-based measures** of low-value services assessed in 1,360,908 Medicare beneficiaries (2009 data).

**Six Categories**:
1. Low-value cancer screening
2. Low-value diagnostic and preventive testing
3. Low-value preoperative testing
4. Low-value imaging
5. Low-value cardiovascular testing and procedures
6. Other low-value surgical procedures

**Medicare Trends Analysis** (PMID: 33591365):
- Examined 21,045,759 fee-for-service Medicare beneficiaries
- 36.3% received ≥1 of 32 low-value services (2014)
- Decreased to 33.6% by 2018
- Modest but measurable improvement over time

**Medicare Waste Study** (PMID: 32728953):
National cross-sectional analysis of 2017 low-value service use and spending:
- Significant variation across regions
- Low-cost, high-volume services contribute disproportionately to waste

### 5.3 Hospital Administrative Data

**Choosing Wisely-Based Indicators** (PMID: 29506573):
- Assessed 824 recommendations from US, Canada, Australia, UK
- Identified **17 recommendations (15 services)** measurable in hospital administrative data
- Demonstrated feasibility of operationalizing CW recommendations
- Enables benchmarking across hospitals

**International Application** (PMID: 37790076):
China hospital discharge records:
- Demonstrated feasibility in different health systems
- Need for context-appropriate definitions

### 5.4 Health System-Level Measurement

**Actionable Measurement Study** (PMID: 34570170):
- System-level measurement and reporting is **feasible**
- Enables cross-system comparisons
- Reveals broad range of low-value care use
- Actionable for quality improvement initiatives

### 5.5 Specialty-Specific Metrics

**Deprescribing Metrics** (PMID: 35166780):
Development of EVOLV-Rx metric:
- Addresses gap in low-value prescribing measurement
- Scalable for older adults
- Quality indicators for inappropriate medications
- **Important**: Most metrics focus on tests/procedures, not medications

**Low-Value Care Differences** (PMID: 31745849):
Comparison of community health centers vs. private practices:
- Different patterns of high-value and low-value care
- Need for setting-specific measurement

### 5.6 Outcome Measures

**Systematic Review of Outcome Measures** (PMID: 31250366):
Wide variation in measures used to assess intervention impact:
- Process measures (service utilization)
- Clinical outcomes (patient harm/benefit)
- Economic outcomes (costs, savings)
- Patient-reported outcomes
- Provider satisfaction/burnout

**Recommendation**: Need for standardized outcome measurement in de-implementation studies.

---

## 6. Inappropriate Diagnostic Testing and Imaging

### 6.1 Scope of the Problem

**Systematic Review of Diagnostic Testing Overuse** (PMID: 33972387):
- **Substantial overuse** with wide variation
- Prevalence estimates: **0.09% to 97.5%** (high heterogeneity)
- **Most frequently identified low-value tests**:
  1. Preoperative testing
  2. Imaging for non-specific low back pain
  3. Routine blood tests
  4. Thyroid function tests

### 6.2 Imaging Overuse

**Magnitude and Financial Implications** (PMID: 30689863):
Study of three common clinical conditions:

**Lumbar Spine MRI**:
- **>60%** deemed inappropriate (2010 and 2013)
- Persistent high rates despite guidelines

**Shoulder Pain MRI**:
- **>30%** inappropriate

**Knee Pain MRI**:
- **>30%** inappropriate

**Total Costs**: >$586 million in unnecessary imaging for these three conditions alone

**Choosing Wisely Initiative Impact** (PMID: 22928172, 28457815):
- Diagnostic imaging prominent focus
- Multiple specialty societies issued recommendations
- Need for active implementation beyond recommendations

**Specific Imaging Overuse Examples**:

**Thyroid Ultrasound** (PMID: 37288725):
- **10-50%** ordered outside clinical practice recommendations
- Contributes to thyroid cancer overdiagnosis epidemic

**Prostate Cancer Staging** (PMID: 21419444, 30578160):
- Of 6,444 low-risk prostate cancer patients, **36.2%** underwent imaging
- Widespread overuse with significant geographic variation
- Downstream impacts: unnecessary biopsies, treatments

**Headache Imaging**:
- Choosing Wisely target
- Modest decreases observed nationally
- Continued overuse in emergency departments

### 6.3 Factors Associated with Inappropriate Imaging

**Physician Characteristics Study** (PMID: 31974904):
- **Physician experience** highly associated with inappropriate imaging
- **Specialty training** highly associated
- **Self-referral** increases inappropriate imaging
- Suggests need for targeted educational interventions

### 6.4 Consequences of Imaging Overuse

**Harms** (PMID: 30900132):
- Radiation exposure
- Contrast media risks
- Incidental findings requiring follow-up
- Cascade effects
- Financial costs to patients and system
- Anxiety and psychological impact

**Ethical Considerations**:
Overdiagnosis and overimaging represent ethical issues for radiological protection and patient safety.

### 6.5 Successful Reduction Strategies

**Evidence-Based Interventions**:
1. Clinical decision support at order entry
2. Prior authorization (effective but potentially burdensome)
3. Audit and feedback to ordering providers
4. Education on appropriateness criteria
5. Removal of financial incentives for self-referral

### 6.6 Preoperative Testing

**Qualitative Study** (PMID: 21557104):
Why physicians order unnecessary preoperative tests—**five major themes**:

1. **Practice tradition**: "We've always done it this way"
2. **Belief other physicians want tests**: Anesthesia, surgery, etc.
3. **Medicolegal worries**: Fear of adverse events
4. **Surgical delays/cancellation concerns**: Avoiding day-of-surgery issues
5. **Lack of guideline awareness**: Not knowing evidence

**Multicomponent De-implementation Strategy** (PMID: 39813049):
- 2025 study of low-risk general surgery
- Multicomponent strategy associated with reduction in unnecessary testing
- Sustained improvements observed

**TDF Barriers Assessment** (PMID: 36480568):
Theoretical Domains Framework-guided qualitative study:
- Identified modifiable barriers
- Informed intervention design
- Demonstrated value of theory-driven approach

**Prevalence and Costs in VA** (PMID: 30599426, 36096937, 33956131):
- 49.3% of low-risk procedures preceded by potentially low-value screening tests
- 321,917 tests representing $11,505,170 (Medicare costs)
- Cataract surgery: significant variation and costs in unnecessary testing
- Reduction efforts showed value without adverse outcomes

**ASA Guideline De-Implementation** (PMID: 38549187):
- ACS-NSQIP longitudinal analysis
- De-implementation of laboratory testing in low-risk patients
- Successful without increases in complications

---

## 7. Clinical Decision Support and Technology

### 7.1 Effectiveness of CDS for Reducing Overuse

**Blood Transfusion CDS** (PMID: 26873112):
Interrupted time series analysis:
- **Significant decline** in overuse of RBC transfusion
- Transfusions decreased from **9.4 to 7.8 per 100 patient days**
- Sustainable reduction maintained

**Additional Blood Management Study** (PMID: 25389326, 32034773):
- Real-time CDS for patient blood management
- Transfusions in patients with Hb >8 g/dL decreased from **60% to <30%**
- Annual RBC transfusions reduced by **24%**
- Economic analysis: **£89,304 annual savings** to department

**Laboratory Testing CDS** (PMID: 26029881):
Decision support tool for ceruloplasmin testing:
- Reduced overtesting
- Improved guideline adherence
- Essential for utilization management programs (PMID: 31036278)

**Advanced Imaging Appropriateness** (PMID: 30779671):
Effect on physicians-in-training:
- CDS tools shown to reduce inappropriate imaging orders
- Particularly effective for trainees
- Educational component built in

### 7.2 Broader CDS Evidence

**Systematic Review** (PMID: 27402662):
- Clinical decision support has **solid evidence base**
- Most effective when combined with other strategies
- Performance feedback also promising

**Monitoring CDS Interventions** (PMID: 29514353):
Emphasizes value of:
- Continuous monitoring of CDS effectiveness
- Iterative refinement based on data
- Measuring both process and outcomes

### 7.3 Alert Fatigue and Optimization

**The Alert Fatigue Problem** (PMID: 27350464):

**Prevalence**: **33% to 96%** of clinical alerts are ignored

**Contributing Factors** (PMID: 28395667):
- Workload (indirect effect)
- Work complexity
- **Repeated alerts** (strongest predictor)
- Alert appropriateness
- Clinician experience

**Optimization Strategies** (PMID: 33186438):
Systematic review of hospital-reported strategies:

**Most Common Approaches**:
1. **Multidisciplinary committee**: Most frequently reported
   - Reviews clinician feedback
   - Analyzes alert data
   - References literature
   - Makes optimization decisions

2. **Alert tiering and classification**:
   - Severe/moderate/minor levels
   - Active vs. passive alerts
   - Only critical alerts interruptive

3. **Default settings modifications**:
   - Leverage behavioral economics
   - Smart defaults reduce unnecessary orders

4. **Evidence-based filtering**:
   - Remove alerts with low positive predictive value
   - Focus on high-yield alerts

**Successful Optimization Example** (PMID: 38086417):
- Replaced burdensome interruptive alert with passive CDS
- Maintained safety
- Reduced clinician burden
- CDS governance and iterative design critical

**Alert Appropriateness Review** (PMID: 24940129):
Framework for evaluating alert appropriateness:
- Clinical relevance
- Actionability
- Timing
- Presentation format

**Refining Clinical Phenotypes** (PMID: 37437601):
- Better patient targeting reduces irrelevant alerts
- Feasibility study showed promise
- Precision in who receives alerts matters

**Semi-Automated CDS** (PMID: 37454289):
- Quantitative evaluation and end-user survey
- Balance between automation and clinician control
- User satisfaction improved

**Safety vs. Alert Fatigue Trade-offs** (PMID: 32620948):
National evaluation of medication-related CDS:
- Tension between maximizing safety and minimizing fatigue
- Need for optimization balancing both
- Not all alerts equal in value

### 7.4 AI and Machine Learning Considerations

**Will AI Contribute to Overuse?** (PMID: 28410309):
Important cautionary article raising concerns:
- AI could amplify existing overuse patterns if trained on current practice
- Risk of automating inappropriate care
- Need for careful design and validation
- Importance of embedding appropriate use criteria

**AI Resolving Information Overload** (PMID: 38218231):
- Biomedical information doubles every ~2 months
- AI can help process data, determine diagnoses, recommend treatments
- Potential to support evidence-based decisions

**Predictive Analytics Applications**:
- **Medication overuse prediction** (PMID: 32637046): ML to predict medication overuse in migraine
- **No-show prediction** (PMID: 32901567): Reduced MRI no-shows from 19.3% to 15.9% (17.2% improvement)

**How AI Can Help "Choose Wisely"** (PMID: 33879255):
Commentary on potential:
- Evidence synthesis at point of care
- Pattern recognition for overuse
- Decision support optimization
- Real-time appropriateness assessment

**Critical Considerations for AI Implementation**:
1. Training data quality (avoid learning from overuse patterns)
2. Integration with clinical workflow
3. Transparency and explainability
4. Alert optimization to prevent fatigue
5. Equity considerations
6. Continuous monitoring and refinement

---

## 8. Audit and Feedback

### 8.1 Overview and Effectiveness

**Cochrane Review** (PMID: 22696318):
- Audit and feedback **generally leads to small but potentially important** improvements
- Median absolute improvement: ~4%
- Effect sizes vary widely based on implementation

**Updated Evidence** (PMID: 12917891):
- Long-standing evidence for audit and feedback
- Effective across diverse clinical contexts
- Sustainability requires ongoing effort

### 8.2 Optimizing Audit and Feedback for Low-Value Care

**Optimization Framework** (PMID: 36066538):
Article specifically addressing A&F for reducing low-value care:
- Tailored approach needed for de-implementation
- Different from promoting new practices
- Must address resistance to change

**Recommendations for De-Implementation** (PMID: 30654620):
Specific recommendations for using A&F to de-implement low-value care:

**Best Practices**:
1. **Feedback source**: Supervisor or colleague more effective than external
2. **Frequency**: More than once (repeated feedback)
3. **Format**: Both verbal and written
4. **Content**: Include explicit targets and action plan
5. **Baseline performance**: More effective when baseline performance is low
6. **Timeliness**: Provide feedback close to the behavior
7. **Benchmarking**: Comparison to peers enhances impact

### 8.3 Audit and Feedback Mechanisms

**Realist Study** (PMID: 38082301):
Implementation strategy mechanisms for reducing clinical variation:
- Social influence through peer comparison
- Professional accountability
- Reflective practice stimulation
- Knowledge gaps identification

### 8.4 Cost-Effectiveness

**Trauma Quality Assurance Program** (PMID: 38632593):
- A&F targeting low-value clinical practices
- Associated with **higher costs and higher effectiveness** than status quo
- **Potential to be cost-effective** at reasonable willingness-to-pay thresholds
- Significant improvements in compliance with evidence-based care
- De-adoption of low-value practices observed

### 8.5 Specialty-Specific Applications

**Quality Circles with A&F** (PMID: 33555552):
Physician assessment and feedback during quality circles:
- Pre-post quality improvement study
- **Modest but statistically significant** effect in reducing low-value services
- Outpatient setting
- Peer-to-peer format valued

**Process Evaluation: Improving Wisely** (PMID: 33514362):
Peer-to-peer data intervention in surgery:
- Process evaluation revealed key mechanisms
- Peer comparison particularly motivating
- Data quality and presentation critical

### 8.6 Challenges and Failures

**Internet-Based A&F Failure** (PMID: 15831542):
- Internet-based A&F failed to improve quality in primary care residents
- Highlights importance of:
  - Delivery format
  - Engagement strategies
  - Contextual factors
  - Target audience characteristics

**Lessons**: Passive, web-based feedback insufficient; active engagement necessary.

### 8.7 Improving Quality of A&F

**General Guidance** (PMID: 22607640):
Improving quality of care through improved A&F:
- Clear, actionable feedback
- Relevant to clinicians' practice
- Timely delivery
- Incorporate behavior change theory
- Engage clinicians in design

### 8.8 Patient-Collected Audio A&F

**Novel Approach** (PMID: 32735338):
VA health system study:
- Patient-collected audio analyzed for clinician attention to life context
- Impact on healthcare costs examined
- Innovative feedback source
- Addresses patient-centeredness

---

## 9. Behavioral Economics and Nudges

### 9.1 Foundational Concepts

**Behavioral Economics in Healthcare** (PMID: 23297657):
Core principles applicable to reducing overuse:
- **Defaults**: People tend to accept default options
- **Framing**: How choices are presented affects decisions
- **Social norms**: Comparison to peers influences behavior
- **Loss aversion**: Losses loom larger than equivalent gains
- **Salience**: Making certain information more prominent

**Nudging Toward Lower Spending** (PMID: 23569045):
- Behavioral economics can help nudge patients and providers
- Approaches could slow health spending growth
- Complements other interventions

### 9.2 Evidence from Randomized Trials

**Committing to Choose Wisely Trial** (PMID: 38285565):
Stepped-wedge cluster RCT (2024):

**Intervention Components**:
- Increased salience of potential harms
- Conveyed social norms
- Promoted professional accountability

**Results**:
- Low-value service use reduced from **20.5% to 16.0%**
- Adjusted OR: **0.79 (95% CI: 0.65-0.97)**
- Also increased **deintensification** of hypoglycemic medications for diabetes
- Demonstrated effectiveness across 3 common clinical situations
- 8 primary care clinics, 18-month follow-up

**Significance**: Largest RCT demonstrating behavioral economics effectiveness for reducing low-value care

### 9.3 Systematic Review of BE Interventions

**Physician Behavioral Change Review** (PMID: 32497082):
Systematic literature review of BE-informed interventions:

**Most Studied Interventions**:
1. **Changing default settings**: Most widely studied, consistently effective
2. **Social reference points/peer comparison**: Consistently effective
3. **Commitment devices**
4. **Framing of information**

**Target Behaviors**:
- **Prescribing behavior**: Most frequently targeted
- Consistently effective interventions across studies
- Particularly successful for antibiotic prescribing

### 9.4 Ethics of Nudging

**Ethical Considerations** (PMID: 22304506):
Examination of ethics in using "nudge" for healthcare:

**Ethically Relevant Dimensions**:
1. Transparency: Should patients/clinicians know they're being nudged?
2. Autonomy: Does nudging respect individual choice?
3. Intent: Whose interests are served?
4. Effectiveness: Does it achieve intended outcomes?

**Conclusion**: Nudges can be ethical when transparent, autonomy-preserving, and patient-centered.

### 9.5 Limitations of Financial Incentives

**Why Money Alone Can't Nudge** (PMID: 30074931):
- Financial incentives alone insufficient for physician behavioral change
- Role of behavioral economics in designing physician incentives
- Intrinsic motivation matters
- Professional norms powerful

**BE Holds Potential** (PMID: 23836740):
- Can deliver better results for patients, insurers, employers
- More nuanced than simple financial incentives
- Potential to increase patient engagement

### 9.6 Application to Type 2 Diabetes Prevention

**Nudging for Diabetes Prevention** (PMID: 30510385):
- Using BE theory to move people toward effective T2D prevention
- Engaging both patients and healthcare partners
- Multi-level intervention design

### 9.7 Design Considerations

**Getting Nudges Right**:
1. **Understand cognitive biases** affecting target behavior
2. **Test interventions** rigorously (RCTs when possible)
3. **Monitor unintended consequences**
4. **Combine with other strategies** (multicomponent approach)
5. **Ensure ethical implementation** (transparency, autonomy)
6. **Tailor to context** (what works varies by setting)

---

## 10. Order Sets and CPOE Systems

### 10.1 Impact on Low-Value Ordering

**Urine Culture Testing** (PMID: 30786940):
Large academic medical center analysis:
- Changes to order sets and urine culture reflex tests
- **45% reduction** in urine cultures ordered
- CPOE system format plays vital role
- Reduced burden of unnecessary urine cultures

**Laboratory Orders Generally** (PMID: 14728436):
- CPOE order sets impact lab orders significantly
- Default settings drive ordering habits (PMID: 25838968)
- Opportunity for reducing low-value testing

### 10.2 Medication Appropriateness

**Preventing PIMs in Hospitalized Older Patients** (PMID: 20696957):
CPOE warning system study:
- Rate of non-recommended medication orders dropped from **11.56 to 9.94 per day**
- Specific alerts embedded in CPOE for patients ≥65 years
- Decreased PIMs **quickly and specifically**
- Demonstrates feasibility of age-specific interventions

### 10.3 Blood Transfusions

**Provider Education + CPOE Alerts** (PMID: 28050312):
Combined intervention study:

**Education Alone Results**:
- Pre-transfusion Hb >8 g/dL: 16.64% → 6.36%
- Post-transfusion Hb >10 g/dL: 14.03% → 3.78%
- Non-emergent 2-unit orders: 45.26% → 22.66%

**Adding CPOE Alerts**: Further improvements
**Lesson**: Education + technology > either alone

### 10.4 Targeted Design Changes

**Acute Asthma Exacerbation** (PMID: 23616900):
- Targeted design changes in CPOE order sets
- Reduction in clinical variance
- Impact on hospitalized children
- Evidence-based care increased

### 10.5 Default Settings and Behavioral Economics

**Default Settings Drive Behavior** (PMID: 25838968):
- Default settings significantly influence physician test selection
- Behavioral economics principle: defaults matter
- Opportunity to "choose" appropriate defaults
- Passive intervention with substantial impact

### 10.6 Standardized Order Sets Evidence

**Systematic Review** (PMID: 31525009):
Review of clinical evidence for standardized hospital order sets:

**Potential Benefits**:
- Reduce medication errors
- Reduce unnecessary clarification calls
- Increase evidence-based care use
- Increase efficient workflow

**Applies to**: Both electronic and paper orders

### 10.7 Reducing Cognitive Workload

**Optimizing Order Sets** (PMID: 23920654):
- CPOE can increase provider cognitive workload
- Optimized order sets can reduce burden
- Balance between comprehensiveness and usability
- User-centered design principles important

### 10.8 Safety Considerations

**Chemotherapy Order Errors** (PMID: 24003174):
- CPOE reduced chemotherapy order errors
- High-risk medications benefit from structured ordering
- Safety and appropriateness can align

### 10.9 Design Principles for Low-Value Care Reduction

**Best Practices**:
1. **Evidence-based defaults**: Set defaults to evidence-based choices
2. **Remove low-value options**: When clearly contraindicated
3. **Require justification**: For low-value choices (soft stop)
4. **Provide context**: Brief evidence at point of decision
5. **Enable appropriate ordering**: Don't make right choice harder
6. **Monitor and refine**: Track ordering patterns, iterate
7. **Engage clinicians**: Co-design with end users

---

## 11. Specific Clinical Areas of Low-Value Care

### 11.1 Antibiotic Overuse and Stewardship

**Scope of the Problem**:
- 39% of urgent care visits result in antibiotic prescriptions
- Major contributor to antimicrobial resistance
- Significant overuse for viral infections, asymptomatic bacteriuria

**Outpatient UTI Stewardship** (PMID: 38575491):
- Inappropriate antibiotic choice or duration common
- Major contributor to antibiotic overuse
- Effective stewardship interventions available

**Hospital Discharge** (PMID: 34554249):
"Reducing Overuse of Antibiotics at Discharge Home" Framework:
- >1 in 8 patients receive antimicrobials at discharge
- **~50% could be improved**
- Discharge increasingly recognized source of overuse

**Broad-Spectrum Antibiotic Overuse** (PMID: 33477994):
Qualitative study across UK, Sri Lanka, South Africa:
- Drivers vary by context
- Stewardship programs focus on reducing BSA use
- Behavior change interventions needed

**Overcoming Implementation Barriers** (PMID: 21587070):
Strategies to stem resistance:
- Executive-level planning
- Local cooperation
- Sustained education
- Emphasis on de-escalation
- Use of care bundles

**Delayed Prescribing** (PMID: 35264330):
- Delayed antibiotic prescribing strategy in urgent care
- Practice change to reduce antibiotic use
- Alternative to immediate prescribing

**Successful Example** (PMID: 37127939):
- Tele-COVID rounds and tele-stewardship intervention
- 17 small community hospitals
- Reduced antibiotic use in COVID-19 patients
- Demonstrates telemedicine applications

### 11.2 Proton Pump Inhibitor Overuse

**Narrative Review and Implementation Guide** (PMID: 34197307):
- PPI overuse for stress ulcer prophylaxis common
- Overuse for nonvariceal GI bleeding
- Implementation guide for reduction in hospitals

**Deprescribing Opportunity** (PMID: 33321078):
- Use and misuse of PPIs widespread
- Significant opportunity for deprescribing
- Many patients on long-term PPIs without appropriate indication

**Side Effects of Long-Term Use** (PMID: 29658189):
- Clostridium difficile infection risk
- Bone fractures
- Vitamin B12 deficiency
- Chronic kidney disease
- Community-acquired pneumonia
- Dementia (conflicting evidence)

**Successful Stewardship Programs**:

1. **Pharmacist-Led Program** (PMID: 29434389):
   - Outcomes in both inpatient and outpatient settings
   - Single institution success

2. **Multidisciplinary Implementation** (PMID: 28596229):
   - Pharmacy and internal medicine collaboration
   - Ensures appropriate PPI continuation

3. **Hematology-Oncology Units** (PMID: 31466535):
   - Guideline implementation effective
   - Sustained PPI reduction without increased GI bleeding
   - Reduced C. difficile risk

4. **Multifaceted Academic Hospital Program** (PMID: 33629438):
   - Sustained decrease in PPI consumption 2012-2019
   - Multiple intervention components

5. **Large-Scale Multicomponent Intervention** (PMID: 38604668):
   - Integrated healthcare system
   - Difference-in-difference study design
   - Significant reduction achieved

**IV PPI Overuse** (PMID: 40549584):
- Overuse in treatment of low-risk upper GI bleeding
- Opportunity for stewardship intervention

**Beyond FDA-Approved Duration** (PMID: 40296703):
- Retrospective cohort study
- PPI use exceeding approved duration for peptic ulcer disease
- Lack of reassessment and deprescribing

### 11.3 Cancer Screening Overuse

**Overdiagnosis in Cancer Screening** (PMID: 28765855, 20413742):
- ~25% mammography-detected breast cancers
- ~50% chest x-ray/sputum-detected lung cancers
- ~60% PSA-detected prostate cancers

**Lung Cancer Screening LDCT** (PMID: 24322569, 23208167, 30276415):
- 18.5% of LDCT-detected cancers overdiagnosed in NLST
- 78.9% of bronchioalveolar cancers overdiagnosed
- Slow-growing/indolent cancers ~25% of incident cases
- Ethical considerations substantial (PMID: 30882498, 30882497)

**Breast Cancer** (PMID: 27241117):
- Biology varies by detection method
- May contribute to overdiagnosis
- Screening benefits must be weighed against harms

**Prostate Cancer** (PMID: 24439788):
- Extensive overdiagnosis and overtreatment documented
- Major public health concern
- Active surveillance as alternative

**Thyroid Cancer**:
- >70% overdiagnosed in China
- Global epidemic of thyroid cancer overdiagnosis
- Low-risk thyroid cancer overtreatment (PMID: 31910092)

**Consequences** (PMID: 31024081):
- Biological challenge and clinical dilemma
- Cost, anxiety, morbidity from treatment
- Reduced benefit of screening programs
- Patient harm from unnecessary procedures

### 11.4 Deprescribing and Polypharmacy

**Definition and Process** (PMID: 25798731, 28700758):
- Tapering or stopping drugs to minimize polypharmacy
- Improve patient outcomes
- Discontinuing inappropriate/unnecessary medications

**Evidence Base** (PMID: 37155330):
- Systematic review of RCTs in older adults with polypharmacy
- 92.9% of studies found deprescribing reduced drug number/doses
- Deprescribing is **safe** and reduces medications

**5-Step Deprescribing Protocol** (PMID: 25798731):
1. Ascertain all current drugs and reasons
2. Consider overall drug-induced harm risk
3. Assess each drug's benefit vs. harm
4. Prioritize drugs for discontinuation
5. Implement discontinuation and monitor closely

**Implementation Considerations** (PMID: 36524602):
Scoping review of implementation:
- Limited consideration of implementation factors previously
- Personnel and resource requirements often overlooked
- Most tools require substantial time
- Difficult to implement in routine encounters

**Barriers and Facilitators** (PMID: 37438697):
- Compliance with expert recommendations varies
- System-level support needed
- Patient and provider education critical

**Harms of Polypharmacy**:
- Adverse drug events
- Cognitive and functional impairment
- Increased healthcare costs
- Increased frailty, falls, hospitalizations, mortality

**Deprescribing Networks** (PMID: 38739460):
- National and international deprescribing networks emerging
- Reducing potentially inappropriate polypharmacy
- Sharing best practices and tools

### 11.5 Preoperative Testing (Expanded)

**See Section 6.6 for comprehensive preoperative testing evidence**

**Additional Context**:
- One of most frequently identified low-value practices
- High-volume, low-cost service
- Amenable to standardization and de-implementation

### 11.6 Cardiovascular Care

**AHA Scientific Statement** (PMID: 35189687):
"Strategies to Reduce Low-Value Cardiovascular Care"
- Comprehensive review of low-value practices in cardiology
- Evidence-based strategies for reduction
- Specialty-specific guidance

**Common Low-Value Cardiovascular Practices**:
- Cardiac imaging in low-risk chest pain
- Stress testing in asymptomatic patients
- Telemetry monitoring in low-risk inpatients
- Unnecessary echocardiograms
- Carotid artery imaging in asymptomatic patients

### 11.7 Intensive Care Settings

**Scoping Review** (PMID: 39453490):
Interventions to reduce low-value care in ICU:
- May have important **health, financial, and environmental** co-benefits
- Multiple low-value practices identified
- Significant opportunity for de-implementation

**Canadian ICU Study** (PMID: 30878979):
- Barriers and facilitators in adopting high-value and de-adopting low-value
- Professional autonomy highly valued
- Need for multidisciplinary engagement

### 11.8 Low-Risk Procedures

**Cataract Surgery** (PMID: 33956131, 30907922):
- Substantial low-value preoperative testing
- Variability and costs in VA system
- Successful reduction interventions demonstrated
- Safety-net health system evaluation showed reductions and cost savings

---

## 12. Economic Aspects of Low-Value Care

### 12.1 Magnitude of Waste

**Comprehensive Waste Analysis** (PMID: 31589283):
JAMA 2019 systematic review:

**Total Annual Costs of Waste**: **$760-935 billion** (25% of total healthcare spending)

**Breakdown by Category**:
1. **Pricing failure**: $81.4-91.2 billion in potential savings
2. **Failure of care delivery**: $44.4-97.3 billion
3. **Failure of care coordination**: $29.6-38.2 billion
4. **Overtreatment/low-value care**: $12.8-28.6 billion
5. **Fraud and abuse**: $22.8-30.8 billion

**Total Potential Savings from Interventions**: **$191-286 billion**

**Critical Note**: Even "low-value care" category alone represents tens of billions in waste, and overtreatment likely underestimates true scope.

**Additional Commentary** (PMID: 31589241, 32125396):
- "Is the US simply spinning its wheels?" regarding waste reduction
- Wasteful spending persists despite awareness
- Need for systematic approaches

### 12.2 Low-Cost, High-Volume Services

**Virginia Analysis** (PMID: 28971913):
Study of 44 low-value services in Virginia All-Payer Claims Database:

**Key Finding**: Low-cost, high-volume services contribute **most** to unnecessary spending
- Services ≤$538: Delivered far more frequently
- Combined costs: **65% of total** low-value spending
- Services ≥$539: Only **35% of total** spending

**Implication**: Interventions should target common, lower-cost services, not just expensive procedures

### 12.3 Medicare Spending

**National Cross-Sectional Analysis** (PMID: 32728953):
2017 Medicare low-value service use and spending:
- Wide variation across regions
- Substantial total spending
- Opportunity for targeted interventions

**Trends 2014-2018** (PMID: 33591365):
- Modest decrease from 36.3% to 33.6% receiving ≥1 low-value service
- Demonstrates measurable but slow progress
- Need for accelerated de-implementation

### 12.4 Framework for Measuring Economic Impact

**Economic Value Framework** (PMID: 29680091):
- Need to comprehensively estimate magnitude
- Track principal sources of waste
- Enable targeting of high-impact areas

### 12.5 Eliminating Waste: Challenges

**Berwick Commentary** (PMID: 22419800):
"Eliminating waste in US health care"
- Identifies major categories of waste
- Calls for systematic approach
- Cultural and system changes needed

**Progress Review** (PMID: 28174162):
- Ongoing challenge
- Multiple stakeholders must engage
- No single solution

---

## 13. Payment Reform and Financial Incentives

### 13.1 Limitations of Payment Reform Alone

**Maryland Global Budget Study** (PMID: 33027725):
- **No evidence** Maryland hospitals reduced systemic overuse under global budgets
- Met revenue targets through other mechanisms
- **Conclusion**: Global budgets alone **too blunt** to selectively reduce low-value care
- Need for complementary targeted interventions

### 13.2 Episode Payment Models

**Cancer Care Study** (PMID: 25006221):
Results of episode payment model:
- Significant total cost reduction achieved
- **Unexpected finding**: Eliminating chemotherapy drug financial incentives **paradoxically increased** chemotherapy use
- Complexity of incentive design
- Unintended consequences possible

### 13.3 Integrated Care and Bundling

**Payment Incentives for Integrated Care** (PMID: 22397058):
- Bundling, pay-for-performance, gain-sharing
- Encourage value-based healthcare
- Interdisciplinary teams
- ACA promotes these models

### 13.4 Provider Incentive Design

**Beyond Financial Risk** (PMID: 32066143):
- Getting incentives right requires thinking beyond financial risk
- Professional norms matter
- Intrinsic motivation important
- Behavioral economics insights valuable

**Why Money Alone Fails** (PMID: 30074931):
- Money alone can't always "nudge" physicians
- Behavioral economics role in incentive design
- Multiple motivations beyond financial

### 13.5 Pay for Performance

**Beyond P4P** (PMID: 18799554):
- Emerging models of provider payment reform
- Moving beyond simple P4P
- More nuanced approaches needed

**Evidence-Based Financial Incentives** (PMID: 20031826):
- Putting together evidence for healthcare reform
- Need for rigorous evaluation
- Theory-driven design

### 13.6 Unintended Consequences

**Ontario Primary Care Study** (PMID: 30933575):
- "Access bonus" payments examined
- Flowed disproportionately to physicians whose patients had **worse outcomes**
- More ED visits, higher costs
- **Lack of alignment** between payments and intended purpose
- Caution regarding poorly designed incentives

### 13.7 Medicare Payment Reform

**Realigning Incentives** (PMID: 12889751, 26151988):
- Fee-for-service Medicare incentive realignment
- Aligning incentives for better care
- Moving toward value-based payment

### 13.8 International Examples

**Hainan, China** (PMID: 14604613):
- Hospital reimbursement reform
- Addressing government and market failures
- Payment incentives as tool

### 13.9 Key Lessons for Payment Reform

1. **Blunt instruments insufficient**: Global budgets alone don't selectively reduce low-value care
2. **Unintended consequences**: Poorly designed incentives can backfire
3. **Complexity matters**: Simple financial incentives often inadequate
4. **Combine approaches**: Payment reform + other strategies more effective
5. **Monitor outcomes**: Track intended and unintended effects
6. **Consider intrinsic motivation**: Professional norms and values matter
7. **Align all incentives**: Quality metrics, payment, and organizational culture must align

---

## 14. Patient Engagement and Communication

### 14.1 Shared Decision-Making

**More Than Information** (PMID: 27044962):
- Shared decision-making requires **conversation, not just information**
- Patient-clinician interaction creates best course of action
- Individualized to patient and family

**Not Synonymous with Patient-Centered Communication** (PMID: 35337712):
- SDM and patient-centered communication not always co-exist
- Value of integrated training should be explored
- Distinction important for intervention design

**Association with Outcomes** (PMID: 29395026):
- Associated with patient-reported health outcomes
- Impact on healthcare utilization
- Potential mechanism for reducing low-value care (when appropriate)

### 14.2 Patient Decision Aids

**Benefits and Challenges** (PMID: 30652607):
- Support shared decision-making
- Help patients understand options
- Can reduce low-value preference-sensitive care
- Implementation challenges exist

### 14.3 Communication Practices

**Systematic Review** (PMID: 28520201):
Conversation analytic research on practices that encourage/constrain SDM:
- Patients have **limited opportunities** to influence decision-making
- Healthcare provider practices may constrain or encourage participation
- Specific communication behaviors identified

**Enhancing SDM Through Interventions** (PMID: 27044959):
- Carefully designed interventions can enhance SDM
- Target both patient and provider behavior
- Multicomponent approach effective

### 14.4 Special Populations

**Limited Health Literacy** (PMID: 32559237):
Palliative care provider perspective:
- Communication and SDM particularly challenging
- Helpful strategies identified
- Barriers to overcome
- Suggestions for improvement

**Critically Ill Patients** (PMID: 20642362):
- Communication practices in physician decision-making
- Unstable patient with end-stage cancer
- High-stakes decisions about low-value aggressive care

### 14.5 Person-Centered Approach

**Person-Centered SDM** (PMID: 31407417):
- Integrates person-centered care principles
- Holistic approach
- Values, preferences, and context matter

### 14.6 Addressing Medical Overuse Through Communication

**Practical Framework** (PMID: 28459906):
- Understanding and reducing overuse through patient-clinician interaction
- Conceptualizing overuse at interaction level
- Communication strategies to address patient expectations

**Design for Reducing Test Cascades** (PMID: 35177360):
- User-centered design to improve patient-doctor communication
- Addressing drivers of medical test overuse and cascades
- Communication tools can prevent unnecessary testing

### 14.7 Implications for Low-Value Care Reduction

**Key Considerations**:
1. Patients often expect "something to be done"—communication can address this
2. SDM can reduce preference-sensitive low-value care
3. Explaining why tests/treatments aren't needed requires skill
4. Communication training should be integrated with other de-implementation strategies
5. Decision aids can support difficult conversations
6. Person-centered approach respects patient autonomy while reducing unnecessary care

---

## 15. Implementation Science Applications

### 15.1 Key Frameworks

**CFIR (Consolidated Framework for Implementation Research)** (PMID: 19664226, 26269693, 27189233, 36309746):
- Most widely used framework in implementation science
- Five domains: intervention characteristics, outer setting, inner setting, individuals, process
- Updated version (2022) based on user feedback
- Applicable to both implementation and de-implementation

**TDF (Theoretical Domains Framework)** (PMID: 28637486):
- 14 domains covering behavioral determinants
- Useful for identifying barriers/facilitators
- Guides intervention development
- Theory-based approach to understanding behavior change

**Combined Use of CFIR and TDF** (PMID: 28057049):
- Systematic review of combined use
- Complementary purposes:
  - CFIR: Comprehensive implementation determinants
  - TDF: Behavior change and intervention development
- Often used together for comprehensive assessment

**NASSS Framework** (PMID: 37495997):
- For Complex Health Technology (particularly CDSS in hospitals)
- Seven domains: condition, technology, value proposition, adopters, organization, wider context, embedding/adaptation over time
- Addresses complexity and scale

### 15.2 Context and Determinants

**Context Matters** (PMID: 30909897):
Scoping review of determinant frameworks:
- Contextual determinants critical for implementation outcomes
- How context is conceptualized varies
- Context dimensions to consider
- Need for explicit attention to context

**Health Equity Integration** (PMID: 35101088, 34090524):
- Equity lens should be integrated from outset
- Practical guide for incorporating health equity domains
- Implementation and equity barriers should be addressed simultaneously
- Optimize scientific yield and equity

**Policy in Implementation Science** (PMID: 36503520, 37700360):
- "Where is policy?" in dissemination and implementation science
- EPIS framework as case example
- Four basic ways to think about policy
- Often overlooked but critical

### 15.3 Barriers and Facilitators Studies

**Mental Health Interventions in LMICs** (PMID: 35022081):
Using implementation science frameworks:
- 37 constructs across 8 domains
- Systematic approach to identifying barriers/facilitators
- Framework-informed analysis valuable

**Enhanced Recovery Pathways** (PMID: 29344622):
- Systematic review using implementation framework
- Surgery-specific barriers and facilitators
- Multi-level factors identified

**COVID-19 Critical Care Practices** (PMID: 36941593):
- CFIR-guided multicenter qualitative study
- Rapid implementation during pandemic
- Barriers and facilitators in crisis context

### 15.4 Scoping Review of TMFs

**143 Theories, Models, and Frameworks** (PMID: 37726779):
Scoping review characteristics:
- **Purpose**: Most common is identifying barriers/facilitators
- **Usability**: Wide variation
- **Applicability**: Different contexts
- **Testability**: Many lack empirical testing

**Implications**: Rich landscape of frameworks, but guidance needed on selection

### 15.5 Methodological Guidance

**Implementation Science 101** (PMID: 36808925):
- For clinicians and clinical researchers
- Beyond effectiveness to implementation
- Practical introduction
- Bridges research-practice gap

**How Behavioral Economics Contributes** (PMID: 38671508):
- BE lens in implementation science
- Mechanisms of action
- Intervention design insights

### 15.6 Application to Low-Value Care

**De-implementing Wisely** (PMID: 32029572):
- Developing evidence base to reduce low-value care
- Implementation science principles applied to de-implementation
- Research agenda proposed

**Methodological Progress Note** (PMID: 38093492):
- De-implementation of low-value care methodological considerations
- Study design issues
- Measurement challenges
- Future directions

---

## 16. Successful Case Studies and Interventions

### 16.1 Behavioral Economics Intervention

**Committing to Choose Wisely (Details in Section 9.2)**:
- Large stepped-wedge cluster RCT
- 20.5% → 16.0% reduction in low-value care
- Demonstrates real-world effectiveness
- Replicable model

### 16.2 Blood Transfusion Reduction

**CDS + Education Programs (Details in Sections 7.1 and 10.3)**:
- Multiple successful examples
- RBC transfusions reduced 24%
- Sustained improvements
- Cost savings documented (£89,304 annually in one program)
- Combination of education and technology

### 16.3 PPI Stewardship

**Multiple Successful Programs (Details in Section 11.2)**:
- Pharmacist-led interventions effective
- Multidisciplinary approaches successful
- Guideline implementation in hematology-oncology: sustained reduction without increased GI bleeding
- Large-scale multicomponent intervention in integrated system
- Academic hospital: sustained decrease 2012-2019

### 16.4 Urine Culture Testing

**Order Set Modification (Details in Section 10.1)**:
- 45% reduction in urine cultures
- Changes to orderables and reflex tests
- CPOE format critical
- Large academic medical center

### 16.5 Choosing Wisely Canada - TSH Testing

**Primary Care Success (Details in Section 2.2)**:
- Effective reduction in TSH testing
- Retrospective parallel cohort study
- Demonstrates active implementation success
- Population-level impact

### 16.6 Preoperative Testing Reduction

**Multicomponent De-implementation (Details in Section 6.6)**:
- Low-risk general surgery patients
- 2025 study showing effectiveness
- ASA guideline de-implementation without adverse outcomes
- Cataract surgery: sustained reductions with cost savings

### 16.7 Audit and Feedback Programs

**Trauma Quality Assurance (Details in Section 8.4)**:
- Cost-effectiveness demonstrated
- Targeting low-value clinical practices
- Improved compliance with evidence-based care
- De-adoption of low-value practices

**Quality Circles (Details in Section 8.5)**:
- Modest but significant effect
- Outpatient low-value service reduction
- Peer-to-peer format

### 16.8 Antibiotic Stewardship

**Tele-stewardship in Community Hospitals (Details in Section 11.1)**:
- 17 small community hospitals
- Reduced antibiotic use in COVID-19 patients
- Telemedicine application
- Scalable model

**Delayed Prescribing (Details in Section 11.1)**:
- Urgent care practice change
- Reduces immediate antibiotic use
- Alternative approach

### 16.9 10-Step Program

**Practical Approach** (PMID: 34156225):
Authors' 15+ years experience:
- Practical, tested approach
- Effectively integrate LVC reduction into medical systems
- Results reported in peer-reviewed journals
- Replicable framework

**10 Steps** (from article):
1. Identify the low-value care
2. Convene stakeholders
3. Review evidence
4. Understand local context
5. Design multicomponent intervention
6. Pilot test
7. Implement broadly
8. Monitor and provide feedback
9. Sustain improvements
10. Spread to other settings

### 16.10 Bronchiolitis Treatment

**Evidence-Based Algorithm (Details in Section 5)**:
- Point-of-care algorithms and rules
- Significant reduction in therapy overuse
- Reduced treatment variation
- Guideline-based

### 16.11 Health System-Level Interventions

**Accountable Care and Behavioral Science (Details in Section 9.2)**:
- Reducing care overuse in older patients
- Professional norms and accountability
- Cluster RCT showing effectiveness

### 16.12 Key Success Factors Across Case Studies

**Common Elements**:
1. **Multicomponent interventions** (not single-strategy)
2. **Stakeholder engagement** (clinicians, patients, leadership)
3. **Evidence integration** at point of care
4. **Measurement and feedback** on performance
5. **System-level support** (resources, culture, incentives)
6. **Iterative refinement** based on data
7. **Sustainability planning** from outset
8. **Leadership commitment**
9. **Combining education + technology + behavioral strategies**
10. **Tailoring to local context**

---

## 17. Research Gaps and Future Directions

### 17.1 Measurement and Methodology

**Gaps Identified**:
1. **Standardization of low-value care measures** across studies and settings
2. **Outcome measurement heterogeneity** limiting meta-analysis
3. **Long-term sustainability** of interventions poorly studied
4. **Cost-effectiveness analyses** limited despite economic importance
5. **Patient-reported outcomes** in de-implementation research underutilized
6. **Unintended consequences** of interventions rarely assessed systematically

**Future Directions**:
- Develop consensus low-value care measure sets
- Standardize outcome reporting in de-implementation trials
- Long-term follow-up studies (>2 years)
- Economic evaluations with rigorous methods
- Patient experience and harm measurement
- Proactive assessment of potential unintended effects

### 17.2 Implementation Science

**Gaps**:
1. **Context-specific factors** determining intervention success poorly understood
2. **Mechanisms of action** for successful interventions often unclear
3. **Scale-up and spread** from single sites to health systems understudied
4. **Sustainability strategies** need more research
5. **De-implementation frameworks** less developed than implementation frameworks
6. **Integration across frameworks** (CFIR, TDF, ERIC, etc.) needs guidance

**Future Directions**:
- Context-mechanism-outcome evaluations (realist approaches)
- Mediation analyses to understand mechanisms
- Multi-site effectiveness and implementation trials
- Sustainability science applications to low-value care
- De-implementation-specific theory development
- Framework synthesis and selection guidance

### 17.3 Technology and AI

**Gaps**:
1. **AI for reducing low-value care** has minimal evidence base
2. **Alert optimization** for de-implementation understudied
3. **Predictive models** to identify overuse patterns needed
4. **Integration with workflow** remains challenging
5. **Alert fatigue** mitigation strategies require more research
6. **Equity implications** of AI-driven interventions unknown

**Future Directions**:
- Develop and rigorously evaluate AI-based interventions for low-value care reduction
- Optimize CDS specifically for de-implementation (different from implementation)
- Machine learning to predict high-risk situations for overuse
- Human-centered design for AI integration
- Alert fatigue reduction through precision targeting and behavioral economics
- Equity-focused AI development and evaluation
- Explainable AI for clinician trust and learning

### 17.4 Behavioral Economics

**Gaps**:
1. **Long-term effects** of behavioral interventions unknown
2. **Which nudges work best** for which low-value services
3. **Combination strategies** with BE components understudied
4. **Patient-directed** behavioral interventions rare
5. **Ethical frameworks** for nudging in healthcare need development
6. **Backfire effects** and reactance possible but understudied

**Future Directions**:
- Multi-year follow-up of BE interventions
- Matching nudges to specific clinical contexts
- Factorial trials testing BE component combinations
- Patient-facing nudge interventions
- Bioethics research on nudging transparency and consent
- Monitoring for and mitigating backfire effects

### 17.5 Health Equity

**Gaps**:
1. **Disparities in low-value care** delivery understudied
2. **Differential intervention effects** by race, ethnicity, SES unknown
3. **Equity of de-implementation** (who benefits?) rarely assessed
4. **Culturally tailored** interventions lacking
5. **Health literacy** considerations in de-implementation minimal
6. **Safety net settings** underrepresented in research

**Future Directions**:
- Describe patterns of low-value care across demographic groups
- Report intervention effects stratified by equity-relevant variables
- Equity impact assessments for all de-implementation interventions
- Cultural adaptation of evidence-based interventions
- Health literacy-informed intervention design
- Partnership with safety net institutions for research

### 17.6 Specific Clinical Areas

**Gaps by Area**:

**Medications**:
- Deprescribing for specific drug classes needs more RCT evidence
- Polypharmacy measurement standardization lacking
- Long-term outcomes of deprescribing unknown for many medications

**Diagnostic Testing**:
- Limited evidence on reducing low-value testing in outpatient settings
- Patient communication strategies for test refusal understudied
- Cascade effect measurement and interruption needs research

**Procedures**:
- De-implementation of low-value procedures (vs. medications/tests) has less evidence
- Surgeon-specific interventions understudied
- Alternative management strategies need evaluation

**Cancer Screening**:
- Communicating overdiagnosis risk to patients remains challenging
- Optimal screening strategies balancing benefits/harms need refinement
- De-implementation of screening in populations where harms exceed benefits

### 17.7 Payment and Policy

**Gaps**:
1. **Payment models** that effectively incentivize low-value care reduction lacking
2. **Policy interventions** for de-implementation understudied
3. **Prior authorization** effectiveness and burden trade-offs unclear
4. **Value-based payment** impact on low-value care needs more evidence
5. **Regulatory approaches** underexplored

**Future Directions**:
- Design and test novel payment models rewarding appropriate restraint
- Natural experiments of policy changes affecting low-value care
- Rigorous evaluation of prior authorization programs
- Longitudinal studies of value-based payment transitions
- International comparisons of regulatory approaches

### 17.8 Patient and Clinician Perspectives

**Gaps**:
1. **Patient preferences** regarding low-value care reduction understudied
2. **Clinician concerns** about medicolegal risk need addressing
3. **Moral distress** related to providing low-value care unexplored
4. **Patient-clinician communication** strategies need development
5. **Trust implications** of de-implementation unknown

**Future Directions**:
- Patient preference elicitation on low-value care trade-offs
- Legal/policy solutions to reduce malpractice concerns for appropriate restraint
- Moral distress measurement in context of low-value care
- Communication intervention development and testing
- Trust and satisfaction assessment in de-implementation studies

### 17.9 Cross-Cutting Priorities

**High-Priority Research Areas**:

1. **Implementation science rigor**: Apply rigorous IS methods to de-implementation
2. **Sustainability**: Long-term maintenance of low-value care reductions
3. **Scalability**: Moving from single-site to system-wide change
4. **Equity**: Ensuring de-implementation benefits all populations
5. **Technology**: Leveraging AI and health IT effectively
6. **Payment**: Aligning financial incentives with value
7. **Measurement**: Standardizing metrics and outcomes
8. **Mechanisms**: Understanding how and why interventions work
9. **Patient engagement**: Meaningful patient involvement in de-implementation
10. **Dissemination**: Translating evidence to widespread practice

---

## 18. Implications for AI-Assisted Interventions at Point of Care

### 18.1 Unique Opportunities for AI

**Real-Time Clinical Decision Support**:
- AI can analyze patient-specific data to assess appropriateness at moment of ordering
- Integration with evidence-based guidelines and Choosing Wisely recommendations
- Contextual factors (patient history, prior testing, contraindications) considered automatically
- Personalized risk-benefit assessment beyond simple rule-based CDS

**Predictive Analytics**:
- Identify patients/situations at high risk for low-value care
- Predict likelihood of cascade effects from marginal test results
- Forecast probable outcomes with/without intervention
- Enable proactive rather than reactive interventions

**Behavioral Economics Integration**:
- Smart defaults based on patient characteristics and evidence
- Social norm comparisons (peer benchmarking) automated
- Framing of choices optimized through AI
- Nudges personalized to clinician preferences and behavior patterns

**Audit and Feedback Automation**:
- Real-time monitoring of low-value care patterns
- Automated feedback generation with actionable recommendations
- Peer comparison at individual, team, and system levels
- Trend analysis and early warning systems

**Evidence Synthesis and Delivery**:
- Rapid synthesis of latest evidence on specific low-value practices
- Just-in-time delivery of relevant evidence at point of decision
- Summarization tailored to clinical context and time constraints
- Continuous updating as new evidence emerges

### 18.2 Critical Design Principles

**Alert Fatigue Mitigation** (Based on Section 7.3):

1. **Precision Targeting**:
   - AI can refine patient phenotypes to reduce false-positive alerts
   - Machine learning to predict which alerts will be acted upon
   - Deliver alerts only when genuinely inappropriate ordering detected

2. **Tiered Alert System**:
   - Critical alerts: Interruptive (rare, high-stakes)
   - Moderate alerts: Acknowledge required but non-blocking
   - Minor alerts: Passive display, no action required
   - AI can classify based on patient-specific risk

3. **Learning from Override Patterns**:
   - Analyze when and why clinicians override alerts
   - Refine algorithms based on feedback
   - Reduce alerts consistently overridden with good reason
   - Improve positive predictive value

4. **Actionable Alerts Only**:
   - Provide clear alternative actions
   - One-click order modification when appropriate
   - Avoid alerts that clinicians can't act on

**Workflow Integration**:

1. **Embedded in EHR**: Not separate system requiring context switching
2. **Minimal Clicks**: Reduce cognitive and physical burden
3. **Timing**: Deliver information at optimal decision point
4. **Formatting**: Scannable, clear, concise

**Transparency and Explainability**:

1. **Show Reasoning**: Why is this flagged as low-value?
2. **Evidence Display**: What evidence supports this recommendation?
3. **Confidence Levels**: How certain is the AI's assessment?
4. **Override Documentation**: Allow clinicians to document valid reasons for override

### 18.3 Evidence-Based Features

**Based on Literature Review Findings**:

**Multicomponent Approach**:
- Combine CDS + audit/feedback + educational content + behavioral nudges
- Literature shows multicomponent > single strategy (77% vs 47% success)
- AI can orchestrate multiple intervention components

**Clinician-Targeted**:
- Focus interventions on ordering clinician
- Patient education secondary (though still valuable)
- Literature shows clinician-targeted more effective

**Peer Comparison**:
- Automated benchmarking to similar peers
- Social norms messaging
- Behavioral economics evidence supports this

**Default Optimization**:
- Evidence-based defaults in order sets
- Remove low-value options when contraindicated
- Require justification for low-value choices (soft stops)

**Performance Feedback**:
- Individual, team, and system-level dashboards
- Trend over time
- Actionable insights

### 18.4 Specific AI Applications

**For Inappropriate Imaging**:
- Assess appropriateness against ACR criteria, Choosing Wisely recommendations
- Flag recent similar imaging (avoid duplicates)
- Suggest alternative diagnostic approaches
- Predict yield of proposed imaging

**For Antibiotic Overuse**:
- Assess likelihood of bacterial vs viral infection
- Recommend appropriate antibiotic choice, dose, duration
- Flag potential antibiotic-resistant patterns
- Suggest delayed prescribing when appropriate

**For Preoperative Testing**:
- Risk-stratify surgical patients
- Recommend testing only for high-risk patients/procedures
- Flag unnecessary tests based on guidelines
- Streamline appropriate testing orders

**For Deprescribing**:
- Identify potentially inappropriate medications
- Assess patient-specific risks of continuation
- Suggest deprescribing protocols
- Monitor for withdrawal/rebound effects

**For Cancer Screening**:
- Calculate individualized risk-benefit balance
- Identify patients where harms likely exceed benefits
- Recommend screening intervals based on risk
- Flag overscreening

### 18.5 Equity Considerations

**Ensuring Equitable AI** (Based on Section 15.2):

1. **Training Data Diversity**: Include diverse patient populations
2. **Bias Detection and Mitigation**: Test for differential performance by demographic groups
3. **Equitable Access**: Deploy in safety net settings, not just academic centers
4. **Cultural Appropriateness**: Tailor interventions to cultural contexts
5. **Health Literacy**: Design for varying literacy levels
6. **Language**: Support multiple languages
7. **Disparities Monitoring**: Track whether AI reduces or exacerbates disparities

**Avoid Exacerbating Inequities**:
- Some populations may experience more low-value care (over-screening in lower-risk groups)
- Others may experience underuse of beneficial care (undertreatment of pain in minorities)
- AI must distinguish low-value from necessary care across populations
- Risk of AI perpetuating biases in training data

### 18.6 Evaluation Framework for AI Interventions

**Process Measures**:
- Alert delivery rates
- Alert acceptance rates (vs override)
- Time to complete orders
- Clinician satisfaction
- System usability scores

**Outcome Measures**:
- Rates of specific low-value services
- Total low-value care index
- Appropriate care maintained or improved
- Patient outcomes (ensure no harm from reduction)
- Healthcare costs
- Cascade effects reduced

**Balancing Measures**:
- Necessary care not inappropriately reduced
- Health disparities not worsened
- Clinician burnout not increased
- Patient satisfaction maintained
- Alert fatigue metrics

**Implementation Measures**:
- Adoption rates across sites/clinicians
- Fidelity to intervention design
- Sustainability over time
- Contextual factors affecting implementation

### 18.7 Challenges and Mitigations

**Challenge 1: Alert Fatigue**
- **Severity**: 33-96% of alerts ignored (PMID: 27350464)
- **Mitigation**: Precision targeting, tiered alerts, learning algorithms, governance

**Challenge 2: Clinician Trust**
- **Concern**: "Black box" AI may be distrusted
- **Mitigation**: Explainability, transparency, clinician involvement in development, option to override

**Challenge 3: Workflow Disruption**
- **Concern**: AI adds time/clicks to already burdened workflows
- **Mitigation**: Seamless EHR integration, minimize clicks, user-centered design

**Challenge 4: Training Data Bias**
- **Concern**: Learning from current practice may learn overuse
- **Mitigation**: Label training data with appropriateness, use evidence-based gold standards, bias audits

**Challenge 5: Medicolegal Concerns**
- **Concern**: Clinicians fear liability for not ordering tests
- **Mitigation**: Document evidence basis, support clinical judgment, system-level backing

**Challenge 6: Patient Expectations**
- **Concern**: Patients may demand low-value services
- **Mitigation**: Patient-facing education, shared decision-making tools, communication support for clinicians

**Challenge 7: Sustainability**
- **Concern**: Initial effects may fade without ongoing support
- **Mitigation**: Continuous monitoring, periodic feedback, algorithm updates, organizational commitment

### 18.8 Implementation Recommendations

**For Healthcare Organizations Deploying AI for Low-Value Care Reduction**:

1. **Start with High-Volume, Low-Controversy Services**:
   - Duplicate imaging within short timeframes
   - Preoperative testing in low-risk patients
   - Inappropriate antibiotic duration
   - Build credibility before tackling contentious areas

2. **Engage Stakeholders Early**:
   - Clinicians (especially potential champions)
   - Patients and patient advocates
   - Administrators and leadership
   - IT and informatics teams
   - Quality and safety committees

3. **Pilot and Iterate**:
   - Small-scale pilots before broad deployment
   - Gather feedback and refine
   - A/B testing of different approaches
   - Measure both intended and unintended effects

4. **Provide Infrastructure Support**:
   - Governance committee for alert optimization
   - Resources for ongoing monitoring and refinement
   - Training for clinicians
   - Communication campaigns

5. **Align Incentives**:
   - Quality metrics reflecting appropriate care (not just volume)
   - Payment models supporting value over volume
   - Recognition for clinicians reducing low-value care
   - Protect from medicolegal risk for appropriate restraint

6. **Measure Rigorously**:
   - Baseline assessment
   - Process, outcome, and balancing measures
   - Equity stratification
   - Long-term sustainability

7. **Plan for Sustainability**:
   - Continuous evidence updates
   - Algorithm refinement based on local data
   - Ongoing clinician engagement
   - Integration into organizational culture

### 18.9 Research Priorities for AI in Low-Value Care Reduction

**High Priority**:
1. Rigorous RCTs of AI-based interventions vs standard CDS
2. Comparative effectiveness of different AI approaches
3. Long-term sustainability of AI interventions
4. Equity impact assessments
5. Cost-effectiveness analyses
6. Unintended consequences (both harms and benefits)
7. Mechanisms of effectiveness (how does AI work?)
8. Optimal alert design and delivery
9. Clinician and patient acceptance
10. Scalability and spread

**Study Designs Needed**:
- Cluster randomized trials (randomize by clinician or clinic)
- Stepped-wedge designs (sequential rollout with evaluation)
- Interrupted time series (before-after with trend analysis)
- Implementation-effectiveness hybrid designs
- Mixed methods (quantitative outcomes + qualitative insights)
- Economic evaluations alongside effectiveness trials

---

## 19. Conclusion

Low-value care represents a massive challenge to healthcare quality and sustainability, consuming approximately 25% of healthcare spending ($760-935 billion annually in the US alone). This foundational literature review, based on comprehensive PubMed-indexed research, identifies clear evidence for what works, what doesn't, and critical gaps requiring further investigation.

### Key Takeaways:

1. **Multicomponent interventions** targeting clinicians are most effective, combining clinical decision support, audit and feedback, behavioral economics, and system changes.

2. **Passive dissemination alone fails**; active implementation strategies are required to achieve meaningful reductions in low-value care.

3. **Barriers are multi-level**, spanning individual (knowledge, attitudes), social (norms, expectations), organizational (resources, culture), and economic/political (incentives, regulations) contexts.

4. **Measurement is feasible** but requires standardization; 26+ claims-based measures exist for Medicare, and Choosing Wisely recommendations can be operationalized.

5. **Technology holds promise** but must be carefully designed to avoid alert fatigue, ensure equity, and integrate with clinical workflows.

6. **Behavioral economics** offers powerful tools—defaults, social norms, accountability—that can reduce low-value care when rigorously applied.

7. **Patient engagement** through shared decision-making and communication is essential, particularly for preference-sensitive services.

8. **Implementation science frameworks** (CFIR, TDF, ERIC) provide structured approaches to identifying barriers, selecting strategies, and evaluating interventions.

9. **Specific clinical areas**—antibiotic overuse, inappropriate imaging, preoperative testing, PPI overuse, cancer screening, polypharmacy—have robust evidence bases for targeted interventions.

10. **Equity must be central**; de-implementation interventions should be designed, evaluated, and refined with explicit attention to health disparities.

### For AI-Assisted Interventions:

AI systems have unique potential to operationalize evidence at the point of care, but success requires:
- **Precision**: Targeting alerts to genuinely inappropriate situations
- **Integration**: Seamless workflow embedding
- **Transparency**: Explainable recommendations clinicians can trust
- **Equity**: Careful attention to bias and disparities
- **Multicomponent design**: Combining CDS, audit/feedback, behavioral nudges, and education
- **Continuous refinement**: Learning from usage patterns and outcomes
- **Rigorous evaluation**: RCTs and implementation studies to build the evidence base

The research literature provides a strong foundation for developing, implementing, and evaluating AI-assisted interventions to reduce low-value care. However, significant research gaps remain, particularly regarding long-term sustainability, equity impacts, optimal design features, and real-world effectiveness of AI specifically applied to this challenge.

Organizations building AI systems to reduce low-value care should ground their work in this evidence base, employ implementation science principles, engage diverse stakeholders, evaluate rigorously, and commit to continuous improvement based on data. The opportunity to improve quality, reduce waste, and enhance patient outcomes is substantial—but realizing this potential requires evidence-based, equity-focused, and thoughtfully implemented approaches.

---

## References

**Note**: This literature review is based on 100+ peer-reviewed publications indexed in PubMed. References are cited throughout by PMID (PubMed ID). To access any cited article, visit: `https://pubmed.ncbi.nlm.nih.gov/[PMID]/`

### Key Systematic Reviews and Meta-Analyses:

- PMID: 34402553 - Impact of Choosing Wisely Interventions (Systematic Review)
- PMID: 27402662 - Interventions to Reduce Low-Value Health Services (Systematic Review)
- PMID: 37428942 - Analysis of 121 Randomized De-implementation Studies
- PMID: 39103927 - De-implementation Effectiveness (Overview of Systematic Reviews)
- PMID: 33972387 - Diagnostic Testing Overuse (Systematic Review)
- PMID: 33127636 - Barriers and Facilitators (Qualitative Evidence Synthesis)
- PMID: 31589283 - Waste in US Healthcare System
- PMID: 22696318 - Audit and Feedback (Cochrane Review)
- PMID: 32497082 - Behavioral Economics Interventions (Systematic Review)
- PMID: 34819122 - De-implementation Frameworks (Scoping Review)
- PMID: 36303219 - De-implementation Strategies (Scoping Review)

### Landmark Studies:

- PMID: 38285565 - Committing to Choose Wisely RCT (Behavioral Economics)
- PMID: 31589283 - $760-935 Billion Waste Estimate
- PMID: 28877170 - Overtreatment in the United States
- PMID: 24819824 - Measuring Low-Value Care in Medicare (26 Measures)
- PMID: 11694107 - Clinical Inertia (Seminal Definition)

### Framework and Theory Papers:

- PMID: 19664226 - CFIR Original Publication
- PMID: 28637486 - TDF Application Guide
- PMID: 28057049 - Combined CFIR and TDF Use
- PMID: 29680091 - Framework for Measuring Low-Value Care

### Clinical Area-Specific:

- PMID: 34197307 - PPI Overuse (Narrative Review and Implementation Guide)
- PMID: 38575491 - Antibiotic Stewardship for UTI
- PMID: 30689863 - Imaging Overuse (Magnitude and Costs)
- PMID: 28765855 - Cancer Screening Overdiagnosis
- PMID: 25798731 - Deprescribing Process

**Full reference list available in PubMed. This review synthesized evidence from 100+ peer-reviewed articles published 2001-2025, with emphasis on recent (2015-2025) high-quality evidence.**

---

**Document End**

*This literature review was conducted in November 2025 for a company building AI systems to reduce low-value care at the point of care. It should be updated periodically as new evidence emerges.*
