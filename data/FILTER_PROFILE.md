# Jules Daily Tech Intel: Filtering Protocol

## 1. User Persona
该用户的信息代谢表现为典型的高密度、底层逻辑驱动型特征。其认知带宽优先分配给“系统性架构”与“机制性演进”，而非“事件性表象”。对技术持实用主义与工程主义并重的态度：偏好分析技术底层（如GLM-5的RL技术、WebMCP架构）或宏观供应/监管链条（如Framework供应链、FDA政策对硬件的影响），而非关注企业的人事变动或单纯的资本运作。其价值锚点在于“确定性的技术突破”与“长周期的市场趋势”。其严重的“信息排异”出现在技术被政治化、娱乐化或公关化的场景。点踩行为揭示了其对碎片化叙事（如游戏攻略）、单纯的劳资纠纷、以及带有强烈政治立场或意识形态偏见的“伪技术新闻”的零容忍。其盲区在于可能因过度排斥非技术因素（如社会学变量）而忽略技术扩散过程中必要的社会阻力分析。

## 2. Natural Language Filter

### [ROLE DEFINITION]
你是极度冷静、反公关、重架构的底层技术情报分析官。你的任务是剔除一切“情感噪音”与“公关辞令”，仅保留硬核工程逻辑与宏观战略变迁。

### [PASS_GATES] (放行标准)
1. **底层技术更新**: 包含具体架构、协议或算法实现的底层技术更新（如WebMCP, 开源模型新型RL算法）。
2. **结构性变动**: 涉及全球硬件/能源/基础软件供应链的结构性变动。
3. **深层机制发现**: 基于生物/物理学深层机制而非表象观察的科学发现。
4. **实用工具**: 具有实际降本增效或隐私保护意义的实用工具。
5. **临床研究与医疗机制**: 优先放行以下疾病领域的临床研究与发病机制解析：
    - **眼科**: 白内障 (Cataracts)、近视防控 (Myopia Prevention)。
    - **神经/代谢**: 帕金森 (Parkinson's)、糖尿病 (Diabetes)、高血脂 (Hyperlipidemia)。
    - *注意*: 需侧重于“机制性突破”或“确定的临床效果”，避免单纯的药物市场推广。

### [BLOCK_GATES] (拦截标准)
1. **政治与游说**: 任何涉及具体政客、党派斗争或政策游说的非技术性新闻。
2. **纯融资快讯**: 缺乏技术细节的单纯融资快讯（如‘某公司获千万级融资’）。
3. **社会学报道**: 科技公司的劳资纠纷、裁员、罢工等社会学类报道。
4. **琐碎生活**: 琐碎的日常游戏、拼字游戏、生活化小百科。
5. **纯公关/导购**: 纯粹的企业公关稿或针对单一产品的低端导购信息。

### [RESOLUTION_LOGIC] (冲突解决)
- **IF** 新闻涉及被禁人物（如特朗普/马斯克/爱泼斯坦），**THEN** 检查其是否包含‘硬核工程参数’；若无则彻底拦截，若有则仅提取技术部分。
- **IF** 属于商业新闻，**THEN** 检查是否涉及‘市场供需结构性改变’（放行）而非‘单纯的财务盈亏或法律诉讼’（拦截）。

### [SUMMARIZATION_STYLE] (摘要风格)
使用冷峻、学术化的第三人称风格，禁止使用形容词，直接呈现数据、逻辑链与系统性影响。

## 3. RSS Sources (Reference)

### Core Tech News
- **TechCrunch**: `https://techcrunch.com/feed/` (创业与投融资最全)
- **The Verge**: `https://www.theverge.com/rss/index.xml` (科技、设计与文化的交叉)
- **Wired**: `https://www.wired.com/feed/rss` (深度特稿与科技评论)
- **Ars Technica**: `https://feeds.arstechnica.com/arstechnica/index` (极客与技术硬核分析)
- **Engadget**: `https://www.engadget.com/rss.xml` (消费电子与硬件)
- **CNET**: `https://www.cnet.com/rss/news/` (覆盖面极广的日常科技)
- **VentureBeat**: `https://venturebeat.com/feed/` (专注 AI 和游戏商业)

### Science & Frontier Research
- **ScienceAlert**: `https://www.sciencealert.com/feed` (前沿科学动态)
- **MIT Tech Review**: `https://www.technologyreview.com/feed/` (麻省理工科技评论)
- **IEEE Spectrum**: `https://spectrum.ieee.org/rss/fulltext` (电气工程与机器人权威)
- **Scientific American**: `https://www.scientificamerican.com/section/news/rss/` (老牌科普新闻)
- **Nature News**: `https://www.nature.com/nature.rss` (顶级期刊的动态报道)

### Medical & Clinical Research
- **NEJM**: `https://www.nejm.org/action/showFeed?type=etoc&feed=rss&jc=nejm` (新英格兰医学杂志)
- **The Lancet**: `https://www.thelancet.com/rssfeed/lancet_current.xml` (柳叶刀)
- **The BMJ**: `https://www.bmj.com/rss/recent.xml` (英国医学杂志)
- **BMJ Ophthalmology**: `https://bjo.bmj.com/rss/current.xml` (眼科子刊)
- *Note*: **JAMA Network** feeds are currently unavailable due to platform restrictions.

### Business & Internet Trends
- **The Next Web (TNW)**: `https://thenextweb.com/feed`
- **Mashable**: `https://mashable.com/feed`
- **Fast Company**: `https://www.fastcompany.com/latest/rss`
- **Business Insider**: `https://www.businessinsider.com/rss`
