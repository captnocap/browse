# Brain-Computer Interfaces in 2026
## Agent 3 -- WebSearch + Browse Combined

---

## Executive Summary

Brain-computer interfaces (BCIs) have reached an inflection point in early 2026. What was once a neuroscience "parlor trick" confined to research labs has become a competitive, multi-billion-dollar industry with roughly 90 active clinical trials worldwide, multiple FDA breakthrough device designations, and the first FDA-cleared next-generation BCI device. Companies like Neuralink, Synchron, Paradromics, and Precision Neuroscience are moving from feasibility studies toward pivotal trials, while new entrants -- including OpenAI-backed Merge Labs and Gabe Newell's Starfish Neuroscience -- are exploring radically different technological approaches. Meanwhile, the regulatory landscape is rapidly evolving, with UNESCO adopting the first global ethical framework for neurotechnology, US states passing neural data privacy laws, and the US GAO issuing comprehensive policy recommendations. This report synthesizes findings from across the BCI landscape as of February 2026.

---

## 1. Latest Scientific Breakthroughs

### 1.1 Real-Time Speech Synthesis from Brain Signals

UC Davis researchers, working within the BrainGate2 clinical trial, demonstrated a first-of-its-kind brain-to-voice neuroprosthesis that translates brain activity into synthesized speech with a delay of just one-fortieth of a second -- essentially instantaneous. Published in Nature in June 2025, the system allowed an ALS patient to "speak" through a computer in real time, modulate intonation to ask questions (90.5% accuracy), emphasize specific words (95.7% accuracy), and even sing simple melodies. Listeners could understand almost 60% of synthesized words correctly (compared to 4% without the BCI). This builds on the same team's earlier work achieving 97% accuracy in brain-to-text decoding with a 125,000-word vocabulary.

### 1.2 Inner Speech Decoding

Stanford Medicine scientists published a landmark study in Cell (August 2025) demonstrating that inner speech -- silent, internal monologue -- produces clear, decodable patterns in motor cortex regions. Four BrainGate2 participants with severe speech and motor impairments showed that inner speech patterns are a smaller but recognizable version of attempted speech activity. This proof of principle raises the possibility of BCIs that decode what a person intends to think-say, rather than requiring attempted physical speech. It also raises important privacy questions about accidental "leakage" of private thoughts.

### 1.3 Columbia University BISC Chip

Published in Nature Electronics in December 2025, the Biological Interface System to Cortex (BISC) from Columbia University represents a generational leap in BCI hardware. The entire system resides on a single CMOS chip thinned to 50 micrometers, occupying less than 1/1000th the volume of standard implants (~3 mm3 total). Key specifications:

- 65,536 electrodes
- 1,024 simultaneous recording channels
- 16,384 stimulation channels
- 100 Mbps wireless data bandwidth (100x higher than any competing wireless BCI)
- Flexible enough to conform to the brain's surface
- Manufactured using standard semiconductor processes, enabling mass production

Short-term intraoperative studies in human patients are already underway, with planned applications in epilepsy, paralysis, ALS, stroke, and blindness.

### 1.4 Restored Touch Sensation

In January 2025, researchers from the University of Chicago and University of Pittsburgh published results showing that intracortical microstimulation (ICMS) of the somatosensory cortex can create stable, precise artificial touch sensations. Five participants received millions of electrical stimulation pulses over a combined 24 years, with more than half of electrodes still functioning reliably after a decade. Scientists demonstrated the ability to create sensations of object boundaries and sliding motion along the skin, using coordinated multi-electrode stimulation patterns.

### 1.5 Chinese Academy of Sciences Invasive BCI

In December 2025, the Chinese Academy of Sciences (CAS) reported a breakthrough in invasive BCI technology. A quadriplegic man can now steer a wheelchair outdoors and command a robotic dog to retrieve items using thought alone. Key technical achievements include:

- Neural data compression and hybrid decoding improving system performance by 15-20%
- "Neural manifold alignment" technique for stable signal interpretation despite emotional and environmental interference
- Online recalibration during daily activities (no pauses required)
- System delay reduced to under 100 milliseconds (faster than the ~200ms for natural brain-to-action in able-bodied individuals)
- Ultra-thin electrodes less than 1% of a human hair's diameter

Additionally, Chinese researchers developed "NeuroWorm" -- a soft, movable, long-term implantable fiber electrode published in Nature in September 2025, representing a shift from static to dynamic electrode operation.

---

## 2. Major Companies and Their Progress

### 2.1 Neuralink

**Status:** ~20 participants across clinical trials in the US, UK, UAE, and Canada.

Neuralink made substantial progress in 2025:

- **FDA Breakthrough Device Designations** received for both speech restoration technology and "Blindsight" (visual cortex stimulation for blind individuals)
- **Global expansion:** Trials launched at Cleveland Clinic Abu Dhabi (UAE-PRIME study), University College London Hospitals and Newcastle Hospitals (UK), and Toronto's University Health Network (Canada). The first UK participant controlled a computer within hours of implantation.
- **$650 million Series E** funding raised, valuing the company at ~$9 billion. Lead investors include ARK Invest, Sequoia Capital, and Founders Fund.
- **Convoy Project** demonstrated robotic arm control via BCI
- **Next-generation surgical robot** improvements: electrode thread insertion reduced to 1.5 seconds per thread, insertion depths exceeding 50mm, compatibility with 99% of anatomical variations, and 95% reduction in needle cartridge manufacturing costs
- **Roadmap:** 30-patient IDE cohort completion targeted by September 2025; PMA application planned for Q4 2025; Phase 3 trials could begin in 2026; commercial release for paralysis patients anticipated around 2028

### 2.2 Synchron

**Status:** 10 patients implanted across US and Australian clinical trials.

Synchron has positioned itself as the leader in minimally invasive BCIs:

- **COMMAND trial success:** All six US patients met the primary safety endpoint -- no device-related serious adverse events resulting in death or permanent increased disability over one year. This is the first FDA-approved IDE trial of a permanently implanted BCI.
- **$200 million Series D** funding raised in November 2025, bringing total funding to $345 million. Led by Double Point Ventures; investors include ARCH Ventures, Khosla Ventures, Bezos Expeditions, Qatar Investment Authority, and the Australian National Reconstruction Fund.
- **Apple ecosystem integration:** Became the first BCI to achieve native integration with iPhone, iPad, and Apple Vision Pro through Apple's new BCI Human Interface Device (HID) protocol, announced in May 2025. In August 2025, an ALS patient publicly demonstrated thought-controlled iPad navigation.
- **OpenAI ChatGPT integration:** Synchron integrated ChatGPT into its BCI platform, enabling paralyzed users to compose complex responses with a single click rather than typing word by word. Synchron does not share users' brain data with OpenAI.
- **Amazon Alexa connectivity** demonstrated with an implanted patient
- **NVIDIA partnership** for next-generation signal processing
- **Pivotal trial preparation** underway, which could make Stentrode the first commercially scalable implanted BCI

### 2.3 Paradromics

**Status:** FDA-approved clinical trial beginning Q1 2026.

Paradromics emerged as a major competitor in 2025:

- **FDA approval** received in November 2025 for the Connect-One clinical study of its Connexus BCI for speech restoration
- **First in-human recording** completed in June 2025 at the University of Michigan, demonstrating safe temporary implantation during epilepsy surgery. The device was implanted, recorded brain signals, and removed intact in less than 20 minutes.
- **Technical specifications:** 421-electrode modular array with integrated wireless transmitter; delivers an industry-leading 200+ bits per second information transfer rate in preclinical models
- **Connect-One study** will initially enroll two participants at three clinical sites: UC Davis, Massachusetts General Hospital, and University of Michigan
- **Device design:** A 7.5mm-wide BCI inserted 1.5mm into the brain, recording from individual neurons in the motor cortex region controlling lips, tongue, and larynx

### 2.4 Precision Neuroscience

**Status:** FDA 510(k) clearance received, 37 patients tested.

- **FDA 510(k) clearance** granted on March 30, 2025 for the Layer 7 cortical interface -- the first full regulatory clearance for a next-generation wireless BCI
- **Device design:** 1,024-electrode flexible thin-film array (one-fifth the thickness of a human hair) that conforms to the brain surface. Inserted through a slit in the dura without piercing brain tissue.
- **Extended deployment:** Cleared for implantation durations of up to 30 days (previously limited to hours)
- **Clinical partnerships** with Beth Israel Deaconess Medical Center (BIDMC) in 2025
- Co-founded by a Neuralink alumnus

### 2.5 Blackrock Neurotech

**Status:** Most widely used implantable BCI globally.

- **Legacy:** The Utah array has been used in BCI research for 25+ years, powering more implanted participants than any other system. Blackrock celebrated 30,000 cumulative patient days.
- **MoveAgain BCI** received FDA Breakthrough Device Designation
- **Neuralace:** Next-generation flexible electrode lattice with 10,000 channels for less invasive cortical coverage
- **Axon-R:** Non-invasive AR-enabled BCI headset launched in 2025, expanding beyond implantable devices
- **In-home testing:** Paralyzed users are living with Blackrock BCIs in their daily home environments

### 2.6 Merge Labs (New Entrant)

- **$252 million seed round** at $850 million valuation, with OpenAI writing the largest single check
- **Non-implantable approach:** Uses ultrasound and molecular approaches rather than electrodes to interact with neurons, avoiding brain tissue implants entirely
- **Co-founders** include Alex Blania (CEO of Tools for Humanity), founders from Forest Neurotech, and Caltech researcher Mikhail Shapiro
- **OpenAI collaboration** on "scientific foundation models and other frontier tools"
- Additional investors include Bain Capital, Interface Fund, Fifty Years, and Gabe Newell

### 2.7 Starfish Neuroscience

- Backed by Valve CEO **Gabe Newell**, developing minimally invasive brain chips in partnership with IMEC
- **Technical specs:** 32 electrode sites, 1.1 milliwatt power consumption, 2x4mm dimensions, no battery (wireless energy transfer)
- **Target applications:** Medical initially, with gaming applications on the horizon (real-time emotion detection, VR motion sickness suppression)
- First chips anticipated in late 2025

### 2.8 Neuracle Neuroscience (China)

- One of three major companies running BCI clinical trials alongside Neuralink and Synchron
- **NEO system:** Semi-invasive, coin-sized, dura-implanted electrode sheet inspired by cochlear implant methods
- Running two trials in China and one in the US
- Leverages research from Tsinghua University's Neural Engineering Lab
- Demonstrated a paralyzed volunteer using the system to control hand grasp through arm electrode stimulation

---

## 3. Clinical Trials and FDA Approvals

### 3.1 Trial Landscape

As of mid-2025, approximately **90 active BCI trials** are running globally, with about 25 specifically testing implantable BCI devices. The total number of individuals who have ever controlled a computer directly with brain implants is approximately 71 (documented), though this number is growing rapidly as multiple companies expand enrollment.

### 3.2 Key FDA Actions

| Company | FDA Action | Date | Details |
|---------|-----------|------|---------|
| Precision Neuroscience | 510(k) Clearance | March 2025 | Layer 7 cortical interface, up to 30-day implantation |
| Neuralink | Breakthrough Device Designation | 2025 | Speech restoration technology |
| Neuralink | Breakthrough Device Designation | 2025 | Blindsight (visual restoration) |
| Paradromics | IDE Approval | November 2025 | Connect-One clinical study for Connexus BCI |
| Blackrock Neurotech | Breakthrough Device Designation | Previously granted | MoveAgain BCI system |
| Synchron | IDE Trial (COMMAND) | Ongoing | First FDA-approved IDE trial of permanently implanted BCI |

### 3.3 International Expansion

Clinical trials have expanded beyond the US to include Australia (Synchron), the UK (Neuralink), UAE (Neuralink), Canada (Neuralink), and China (Neuracle, CAS). This geographical diversification is accelerating as companies prepare for global regulatory submissions.

---

## 4. Consumer and Commercial Applications

### 4.1 Non-Invasive Consumer BCIs

**Neurable MW75 Neuro LT** -- Consumer-grade BCI headphones ($499) combining premium active noise-cancelling audio with 12 EEG channels. Soft fabric sensors monitor brain activity in real time, tracking focus levels and prompting breaks when concentration drops. Partnership with Master & Dynamic.

**Blackrock Axon-R** -- Non-invasive AR-enabled headset launched in 2025, bridging the gap between implantable and wearable BCIs.

### 4.2 Tech Ecosystem Integration

The most significant commercial development of 2025 was Apple's announcement of a **BCI Human Interface Device (HID) protocol** during Global Accessibility Awareness Day in May 2025. This protocol, rolling out with iOS 19 and iPadOS 19:

- Makes brain signals a native input method for Apple devices for the first time
- Enables closed-loop communication where the device shares contextual screen data with the BCI decoder
- Was demonstrated by Synchron in August 2025 with thought-controlled iPad navigation
- Supports iPhone, iPad, and Apple Vision Pro

Synchron has also demonstrated integration with **Amazon Alexa** and **Apple Vision Pro**, while partnering with **NVIDIA** for signal processing.

### 4.3 AI-Powered Communication

The integration of ChatGPT with Synchron's BCI platform allows paralyzed users to generate contextually relevant responses with minimal input. This represents a convergence of generative AI and neurotechnology that is likely to accelerate.

### 4.4 Gaming and Entertainment

- **Valve/Gabe Newell:** Modified VR headsets incorporating EEG sensors for brain signal reading, with open-source developer tools planned
- **Neuralink participants** are already playing video games (Civilization, chess) using thought control
- Starfish Neuroscience targets gaming applications including adaptive difficulty based on emotion detection

### 4.5 Military and Defense

DARPA has been a major BCI funder since at least 2016 through programs like N3 (Next-Generation Nonsurgical Neurotechnology). Applications under research include monitoring soldier cognitive workload, drone swarm control, and accelerated learning. The US Air Force is working on BCIs using neuromodulation to alter mood and reduce fatigue.

---

## 5. Ethical and Regulatory Landscape

### 5.1 UNESCO Global Framework

In November 2025, UNESCO's General Conference adopted the **Recommendation on the Ethics of Neurotechnology** -- the first global ethical framework for neurotechnology. Key elements include:

- Rights-based framework covering the entire life cycle of neurotechnology (design to disposal)
- Protection of "neural data" as sensitive personal information
- Affirmation of mental privacy as a fundamental concern
- Principles of proportionality, scientific evidence, and human dignity
- While not legally binding, it guides 194 member states, research organizations, and private companies
- Implementation support through Readiness Assessment Methodology, Ethical Impact Assessment frameworks, and capacity-building programs

### 5.2 US State Legislation

The "neurorights" movement has gained significant legislative momentum:

- **Colorado:** Enacted law requiring opt-in consent for neural data collection and use
- **California:** SB 44 (2025-2026 session) proposes amending the California Consumer Privacy Act to require businesses to use neural data only for the purpose for which it was collected through a brain-computer interface
- **Minnesota:** Proposed standalone law (SF 1240) with civil and criminal penalties for neural data rights violations, establishing the right to mental privacy and prohibiting government agencies from collecting brain activity data without informed consent
- **Montana and Connecticut:** Have also enacted neural data protections

### 5.3 Federal US Action

- **The MIND Act (S2925):** Introduced by three US Senators to address concerns about neurotechnology, covering both implantable BCIs and consumer wellness products
- **GAO Report (GAO-25-106952):** "Brain-Computer Interfaces: Applications, Challenges, and Policy Options" identified eight policy options, highlighting gaps in data ownership, long-term patient support after clinical trials end, insurance coverage (including Medicare), and the lack of a unified privacy framework spanning medical and non-medical BCI uses
- **FTC investigation** prompted by senators calling for scrutiny of BCI privacy practices

### 5.4 Key Ethical Concerns

- **Neural data commodification:** Companies developing BCIs may have access to sensitive brain signal data without users' understanding or consent
- **Post-trial abandonment:** Clinical trial participants have had BCIs removed because no funds or medical support existed after the trial ended
- **Consent complexity:** Traditional informed consent frameworks are inadequate for devices that interface directly with cognition
- **Inner speech privacy:** Stanford's discovery that inner speech is decodable from motor cortex raises concerns about accidental disclosure of private thoughts
- **Cognitive enhancement:** Ethical questions about using BCIs for enhancement rather than restoration of lost function
- **Equity and access:** Risk that advanced BCI technologies remain available only to wealthy populations
- **Dual-use concerns:** Military applications of neurotechnology blur ethical boundaries around cognitive liberty

---

## 6. Academic Research Frontiers

### 6.1 AI and Neural Decoding

The convergence of deep learning with neural data has been transformative. Modern BCI decoders achieve 99% word accuracy with less than 0.25-second latency for speech tasks. Key research directions include:

- **Foundation models for neural data:** OpenAI's collaboration with Merge Labs on "scientific foundation models" for BCI
- **DeepSeek integration:** Researchers are exploring synergies between DeepSeek's AI innovations and BCI signal processing
- **Closed-loop neurorehabilitation:** Systematic reviews document advancing AI/ML innovations in closed-loop BCI systems for rehabilitation

### 6.2 Deep Brain Stimulation for Mental Health

A significant frontier is the use of BCIs and deep brain stimulation (DBS) for treatment-resistant depression:

- **Mount Sinai Hospital** performed the first national DBS implant as part of a clinical trial for depression
- An AI model developed by Professor Christopher Rozell at Georgia Tech can identify signs of depression relapse **five weeks** before symptoms appear
- A 100-person trial of closed-loop DBS for depression is underway
- No DBS platform is yet approved for depression, though first-generation devices are approaching approval
- The **Shanghai Mental Health Center** is running the largest non-invasive BCI trial for mental health (400 participants), testing brain-controlled applications for mood regulation in depression and bipolar disorder

### 6.3 Flexible and Dynamic Electrodes

The field is moving beyond static electrode arrays:

- **NeuroWorm** (Chinese Academy of Sciences/Donghua University): A soft, movable, long-term implantable fiber electrode enabling "active, intelligent exploration" of neural tissue rather than passive recording (published in Nature, September 2025)
- **Precision Neuroscience Layer 7:** Ultra-thin flexible film that conforms to the brain surface
- **BISC chip:** Flexible enough to curve to match the brain's surface while maintaining 65,536 electrode contacts

### 6.4 Multimodal BCIs

Researchers are developing BCIs that decode multiple modalities simultaneously:

- One patient has used a multimodal BCI independently at home for **more than two years** without daily recalibration, decoding both attempted speech into text and attempted hand movements, achieving 99% accuracy
- The combination of speech, motor, and sensory feedback in single systems is becoming standard in research settings

---

## 7. Investment and Market Trends

### 7.1 Funding Landscape

BCI funding has surged dramatically:

| Company/Entity | Amount | Round | Valuation | Year |
|----------------|--------|-------|-----------|------|
| Neuralink | $650M | Series E | ~$9B | 2025 |
| Merge Labs | $252M | Seed | $850M | 2026 |
| Synchron | $200M | Series D | Undisclosed | 2025 |
| Precision Neuroscience | $100M+ | Latest round | Undisclosed | 2024 |

Total BCI sector funding **tripled** to $867 million from 2024, driven largely by Neuralink's mega-round. Chinese BCI venture funding in 2025 more than doubled from 2024 levels, raising at least 1.1 billion yuan.

### 7.2 Market Projections

- **2025:** $2.94 billion global market
- **2026:** $3.33 billion (projected)
- **2035:** $13.86 billion (projected), at a CAGR of 16.77%
- Non-invasive BCIs currently dominate revenue share due to accessibility, safety, and broader applicability in rehabilitation and assistive communication

### 7.3 Key Investment Themes

1. **Regulatory milestones as catalysts:** FDA clearances are expected to be the primary driver of 2026 growth, validating investor theses
2. **AI convergence:** Integration of AI (including large language models) with BCI systems is attracting cross-sector investment from tech giants like OpenAI and Apple
3. **Non-invasive vs. invasive debate:** Investors are funding both approaches -- Merge Labs ($252M for non-invasive ultrasound) and Neuralink ($650M for implantable) -- suggesting the market may support multiple technological paradigms
4. **Geographic diversification:** Investment flowing into both US and Chinese BCI ecosystems, with geopolitical competition accelerating development
5. **Defense spending:** DARPA and military applications continue to provide significant R&D funding

### 7.4 Industry Maturation Signals

- Apple building native BCI support into its operating systems
- Synchron's integration with major consumer platforms (Apple, Amazon, NVIDIA)
- Transition from academic-led research to company-led clinical trials
- Multiple companies approaching pivotal (Phase 3-equivalent) trials
- First FDA-cleared next-generation BCI device (Precision Neuroscience Layer 7)

---

## 8. Key Trends to Watch in 2026

1. **Pivotal trials:** Synchron is preparing its pivotal trial for Stentrode, which could lead to the first commercially available implanted BCI. Neuralink may begin Phase 3 trials.
2. **Paradromics enters clinical testing:** The Connect-One study will provide the first long-term human data for the high-bandwidth Connexus device.
3. **Mental health applications:** Brain implants for depression and other psychiatric conditions represent a potential expansion of BCIs beyond motor disability.
4. **Chinese competition:** China is investing heavily, with multiple startups and state-backed research institutions developing competitive technologies. The Chinese government has set 2027 BCI breakthrough targets.
5. **Regulatory evolution:** More US states are expected to pass neural data privacy laws; federal legislation (MIND Act) may advance; UNESCO framework implementation begins.
6. **AI-BCI convergence:** Deeper integration of generative AI models with BCI platforms for improved communication and control.
7. **Flexible electrode technologies:** New materials and designs could reduce tissue damage and improve long-term signal stability.
8. **Consumer BCI market growth:** Non-invasive wearable BCIs for productivity, wellness, and gaming applications are expanding.

---

## 9. Conclusion

The BCI field in early 2026 stands at a genuine inflection point. The convergence of advanced semiconductor technology (BISC chip), AI-powered decoding (99% speech accuracy), regulatory progress (FDA clearances and breakthrough designations), massive investment ($867M in 2025 alone), and major technology company engagement (Apple, OpenAI, NVIDIA) suggests that the long-promised translation from research to product is finally underway. The question is no longer whether BCIs will become clinically available, but how quickly, for whom, and under what regulatory and ethical frameworks. The next 12-24 months will be decisive, as multiple companies approach the pivotal trials that could yield the first commercially approved implanted BCI systems.

---

## Sources

### WebSearch (used for broad discovery and landscape mapping)

1. [MIT Technology Review - Brain-computer interfaces face a critical test](https://www.technologyreview.com/2025/04/01/1114009/brain-computer-interfaces-10-breakthrough-technologies-2025/) -- WebSearch
2. [STAT News - Brain-computer implants are coming of age: 3 trends to watch in 2026](https://www.statnews.com/2025/12/26/brain-computer-interface-technology-trends-2026/) -- WebSearch
3. [ScienceDaily - Scientists reveal a tiny brain chip that streams thoughts in real time](https://www.sciencedaily.com/releases/2025/12/251209234139.htm) -- WebSearch
4. [Chinese Academy of Sciences - Chinese Scientists Make Breakthrough in Invasive BCI Trial](https://english.cas.cn/newsroom/cas_media/202512/t20251219_1138007.shtml) -- WebSearch
5. [Nature - A brain implant that could rival Neuralink's enters clinical trials](https://www.nature.com/articles/d41586-025-03849-0) -- WebSearch
6. [Paradromics - FDA Approval for Connect-One Clinical Study](https://www.paradromics.com/news/paradromics-receives-fda-approval-for-the-connect-one-clinical-study-with-the-connexus-brain-computer-interface) -- WebSearch
7. [CNBC - Neuralink competitor Paradromics completes first human implant](https://www.cnbc.com/2025/06/02/neuralink-paradromics-human-implant.html) -- WebSearch
8. [University of Michigan - First in-human recording with wireless BCI](https://www.michiganmedicine.org/news-release/university-michigan-team-leads-first-human-recording-new-wireless-brain-computer-interface) -- WebSearch
9. [Clinical Trials Arena - Synchron's BCI meets primary endpoint](https://www.clinicaltrialsarena.com/news/synchrons-bci-meets-primary-endpoint-in-feasibility-trial/) -- WebSearch
10. [Fierce Biotech - Synchron raises $200M](https://www.fiercebiotech.com/medtech/synchron-raises-200m-advance-its-brain-computer-interface-paralysis) -- WebSearch
11. [BusinessWire - Synchron Raises $200 Million Series D](https://www.businesswire.com/news/home/20251106150841/en/Synchron-Raises-$200-Million-Series-D-to-Advance-Brain-Computer-Interface-Technology) -- WebSearch
12. [Precedence Research - Brain Computer Interface Market Size](https://www.precedenceresearch.com/brain-computer-interface-market) -- WebSearch
13. [CB Insights - BCI startups race toward commercial deployment](https://www.cbinsights.com/research/leading-brain-computer-interface-startups/) -- WebSearch
14. [TechCrunch - OpenAI invests in Sam Altman's BCI startup Merge Labs](https://techcrunch.com/2026/01/15/openai-invests-in-sam-altmans-brain-computer-interface-startup-merge-labs/) -- WebSearch
15. [Nature - OpenAI-backed firm to use ultrasound to read minds](https://www.nature.com/articles/d41586-026-00329-x) -- WebSearch
16. [OpenAI - Investing in Merge Labs](https://openai.com/index/investing-in-merge-labs/) -- WebSearch
17. [Hypebeast - OpenAI Leads $252 Million Bet on Merge Labs](https://hypebeast.com/2026/1/openai-leads-252-million-bet-on-merge-labs-bcis) -- WebSearch
18. [Neuralink Official Updates](https://neuralink.com/updates/) -- WebSearch
19. [Applying AI - Neuralink to Launch High-Volume Brain Implant Production by 2026](https://applyingai.com/2026/01/neuralink-to-launch-high-volume-brain-implant-production-by-2026-a-deep-dive/) -- WebSearch
20. [MassDevice - Precision Neuroscience wins FDA clearance for BCI](https://www.massdevice.com/precision-neuroscience-fda-clearance-bci-interface/) -- WebSearch
21. [GlobeNewswire - Precision Neuroscience FDA Clearance announcement](https://www.globenewswire.com/news-release/2025/04/17/3063418/0/en/Precision-Neuroscience-Receives-FDA-Clearance-for-High-Resolution-Cortical-Electrode-Array.html) -- WebSearch
22. [Columbia Engineering - Silicon Chips on the Brain](https://www.engineering.columbia.edu/about/news/silicon-chips-brain-researchers-announce-new-generation-brain-computer-interface) -- WebSearch
23. [BusinessWire - Synchron Debuts Thought-Controlled iPad via Apple BCI HID Protocol](https://www.businesswire.com/news/home/20250804537175/en/Synchron-Debuts-First-Thought-Controlled-iPad-Experience-Using-Apples-New-BCI-Human-Interface-Device-Protocol) -- WebSearch
24. [9to5Mac - Apple's brain-controlled iPhone/iPad tech revealed](https://9to5mac.com/2025/08/04/apples-new-brain-controlled-iphone-ipad-tech-revealed-in-video/) -- WebSearch
25. [BusinessWire - Synchron native BCI integration with Apple devices](https://www.businesswire.com/news/home/20250513927084/en/Synchron-To-Achieve-First-Native-Brain-Computer-Interface-Integration-with-iPhone-iPad-and-Apple-Vision-Pro) -- WebSearch
26. [UNESCO - Ethics of Neurotechnology Recommendation](https://www.unesco.org/en/articles/ethics-neurotechnology-unesco-adopts-first-global-standard-cutting-edge-technology) -- WebSearch
27. [Inside Privacy - UNESCO Adopts First Global Framework on Neurotechnology Ethics](https://www.insideprivacy.com/health-privacy/unesco-adopts-first-global-framework-on-neurotechnology-ethics/) -- WebSearch
28. [IAPP - Navigating legal and ethical landscape of BCIs: Colorado and Minnesota](https://iapp.org/news/a/navigating-the-legal-and-ethical-landscape-of-brain-computer-interfaces-insights-from-colorado-and-minnesota) -- WebSearch
29. [Arnold & Porter - Neural Data Privacy Regulation](https://www.arnoldporter.com/en/perspectives/advisories/2025/07/neural-data-privacy-regulation) -- WebSearch
30. [Cooley - The MIND Act: Balancing Innovation and Privacy](https://www.cooley.com/news/insight/2025/2025-09-25-the-mind-act-balancing-innovation-and-privacy-in-neurotechnology) -- WebSearch
31. [GAO - Brain-Computer Interfaces: Applications, Challenges, and Policy Options](https://www.gao.gov/products/gao-25-106952) -- WebSearch
32. [GovTech - California bill would regulate BCI data](https://www.govtech.com/policy/calif-bill-would-regulate-brain-computer-interface-data) -- WebSearch
33. [Mount Sinai - First DBS Implant for Depression Clinical Trial](https://www.mountsinai.org/about/newsroom/2025/mount-sinai-is-first-in-the-nation-to-perform-deep-brain-stimulation-implant-as-part-of-clinical-trial-for-depression) -- WebSearch
34. [IEEE Spectrum - Next-Gen Brain Implants Offer New Hope for Depression](https://spectrum.ieee.org/deep-brain-stimulation-depression) -- WebSearch
35. [ScienceDaily - Patients tried everything for depression then this implant changed their lives](https://www.sciencedaily.com/releases/2026/01/260120000328.htm) -- WebSearch
36. [UChicago Medicine - Fine-tuned BCI makes prosthetic limbs feel more real](https://www.uchicagomedicine.org/forefront/biological-sciences-articles/2025/january/bionic-hand-sensation) -- WebSearch
37. [EurekAlert - A new era of BCIs: Restored touch, accurate speech, seamless movement](https://www.eurekalert.org/news-releases/1106526) -- WebSearch
38. [Neurable - MW75 Neuro LT consumer BCI headphones](https://www.neurable.com/products/mw75neurolt) -- WebSearch
39. [BusinessWire - Neurable launches first smart BCI-enabled headphones](https://www.businesswire.com/news/home/20240924893354/en/Neurable-Inc.-Launches-First-Smart-Brain-Computer-Interface-Enabled-Headphones-for-Consumer-Market) -- WebSearch
40. [Blackrock Neurotech - Record Set for Implantable Brain Tech: 30,000 Patient Days](https://blackrockneurotech.com/insights/record-set-implantable-brain-tech/) -- WebSearch
41. [All Health Tech - From lab to life: Blackrock Neurotech BCI breakthroughs](https://allhealthtech.com/blackrock-neurotech-bci/) -- WebSearch
42. [Tom's Hardware - Gabe Newell's BCI startup to reveal first chips](https://www.tomshardware.com/peripherals/wearable-tech/gabe-newells-brain-computer-interface-startup-to-reveal-first-chips-later-this-year) -- WebSearch
43. [PCWorld - Valve's Gabe Newell is working on a brain chip](https://www.pcworld.com/article/2794946/valves-gabe-newell-is-reportedly-working-on-a-batteryless-brain-chip.html) -- WebSearch
44. [Stanford News - Scientists develop interface that reads thoughts from speech-impaired patients](https://news.stanford.edu/stories/2025/08/study-inner-speech-decoding-device-patients-paralysis) -- WebSearch
45. [Stanford Medicine - Study of promising speech-enabling interface](https://med.stanford.edu/news/all-news/2025/08/brain-computer-interface.html) -- WebSearch
46. [BusinessWire - Synchron announces BCI chat feature powered by OpenAI](https://www.businesswire.com/news/home/20240711493318/en/Synchron-Announces-Brain-Computer-Interface-Chat-Feature-Powered-by-OpenAI) -- WebSearch
47. [Bloomberg - China's Brain Implant Startups Take On Musk's Neuralink](https://www.bloomberg.com/news/articles/2025-09-18/china-s-brain-startups-take-on-musk-s-neuralink-in-new-tech-race) -- WebSearch
48. [Digitimes - China eyes 2027 BCI breakthrough](https://www.digitimes.com/news/a20250811PD223/miit-china-chips-policy-roadmap.html) -- WebSearch

### Browse (used for deeper content extraction from JS-rendered pages)

49. [STAT News - Brain-computer implants are coming of age (paywall preview)](https://www.statnews.com/2025/12/26/brain-computer-interface-technology-trends-2026/) -- Browse
50. [Nature - A brain implant that could rival Neuralink's (paywall preview)](https://www.nature.com/articles/d41586-025-03849-0) -- Browse
51. [MIT Technology Review - Brain-computer interfaces face a critical test (full article)](https://www.technologyreview.com/2025/04/01/1114009/brain-computer-interfaces-10-breakthrough-technologies-2025/) -- Browse
52. [Cerebralink - Neuralink's Milestones in 2025 and Promising Future in 2026 (full article)](https://www.cerebralink.com/post/neuralink-s-milestones-in-2025-and-its-promising-future-in-2026) -- Browse
53. [Andersen Lab - BCIs in 2025: Trials, Progress, and Challenges (full article)](https://andersenlab.com/blueprint/bci-challenges-and-opportunities) -- Browse
54. [GeneOnline - Brain Implants for Mental Health and Chinese Competition](https://www.geneonline.com/brain-implants-for-mental-health-and-chinese-competition-expected-to-shape-bci-advancements-by-2026/) -- Browse
55. [IEEE Spectrum - AI Enhances Deep Brain Stimulation for Depression (partial)](https://spectrum.ieee.org/deep-brain-stimulation-depression) -- Browse
56. [Chinese Academy of Sciences - Chinese Scientists Make Breakthrough in Invasive BCI Trial (full article)](https://english.cas.cn/newsroom/cas_media/202512/t20251219_1138007.shtml) -- Browse
57. [ScienceDaily - Scientists reveal a tiny brain chip (full article)](https://www.sciencedaily.com/releases/2025/12/251209234139.htm) -- Browse
58. [UC Davis Health - First-of-its-kind technology helps man with ALS speak in real time (full article)](https://health.ucdavis.edu/news/headlines/first-of-its-kind-technology-helps-man-with-als-speak-in-real-time/2025/06) -- Browse

---

*Report compiled on February 11, 2026. Agent 3 used a combined approach of WebSearch for broad discovery and landscape mapping (48 sources) and the Browse tool for deeper content extraction from 10 key articles, several of which were JS-rendered, paywalled, or otherwise required full browser access for complete content retrieval.*
