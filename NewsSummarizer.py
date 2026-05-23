import streamlit as st
from dotenv import load_dotenv
from typing import List
from pydantic import BaseModel
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------
st.set_page_config(
    page_title="AI News Intelligence Dashboard",
    page_icon="📰",
    layout="wide"
)

# ---------------------------------------------------
# CSS
# ---------------------------------------------------
st.markdown("""
<style>
.main {
    background-color: #0b1220;
}

.block-container {
    padding-top: 1rem;
}

.stButton > button {
    width: 100%;
    height: 52px;
    border-radius: 14px;
    border: none;
    background: linear-gradient(90deg,#2563eb,#7c3aed);
    color: white;
    font-size: 16px;
    font-weight: 600;
}

.section-card {
    background: #111827;
    padding: 22px;
    border-radius: 18px;
    border: 1px solid #374151;
    margin-bottom: 18px;
}

.entity-chip {
    display: inline-block;
    padding: 8px 14px;
    margin: 5px;
    border-radius: 20px;
    background: #1e293b;
    border: 1px solid #475569;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# DATA SCHEMA
# ---------------------------------------------------
class ImpactAnalysis(BaseModel):
    positive: List[str]
    negative: List[str]


class NewsAnalysis(BaseModel):
    executive_summary: str
    top_headlines: List[str]
    key_developments: List[str]
    impact_analysis: ImpactAnalysis
    risks: List[str]
    entities: List[str]
    takeaways: List[str]


# ---------------------------------------------------
# FUNCTIONS
# ---------------------------------------------------
def fetch_news(query, max_results):
    search_tool = TavilySearchResults(max_results=max_results)
    results = search_tool.invoke(query)

    filtered = [
        item for item in results
        if item.get("content")
    ]

    if not filtered:
        return None, None

    article_text = "\n\n".join(
        item["content"] for item in filtered
    )

    return filtered, article_text


def create_chain(model_name, temperature):
    llm = ChatGroq(
        model=model_name,
        temperature=temperature
    )

    structured_llm = llm.with_structured_output(NewsAnalysis)

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """
You are a professional financial and news intelligence analyst.

Analyze the provided news content and generate accurate structured analysis.
Focus on relevance to the user's query.
Be factual and concise.
"""
        ),
        (
            "human",
            "User query: {query}\n\nNews content:\n{article}"
        )
    ])

    return prompt | structured_llm


# ---------------------------------------------------
# UI
# ---------------------------------------------------
st.title("📰 AI News Intelligence Dashboard")
st.caption("Real-time AI-powered structured news analysis")

st.sidebar.header("⚙ Configuration")

query = st.sidebar.text_input(
    "Search Topic",
    value="indian stock market"
)

max_results = st.sidebar.slider(
    "Number of Articles",
    3,
    10,
    5
)

temperature = st.sidebar.slider(
    "Model Creativity",
    0.0,
    1.0,
    0.2
)

model_name = st.sidebar.selectbox(
    "Select Model",
    [
        "llama-3.3-70b-versatile",
        "mixtral-8x7b-32768"
    ]
)

# ---------------------------------------------------
# BUTTON
# ---------------------------------------------------
if st.button("🚀 Analyze News"):

    if not query.strip():
        st.warning("Please enter a search topic.")
        st.stop()

    with st.spinner("Fetching latest news..."):
        try:
            news_results, article_text = fetch_news(query, max_results)
        except Exception as e:
            st.error(f"News fetch failed: {str(e)}")
            st.stop()

    if not article_text:
        st.warning("No usable articles found.")
        st.stop()

    chain = create_chain(model_name, temperature)

    with st.spinner("Generating analysis..."):
        try:
            data = chain.invoke({
                "query": query,
                "article": article_text
            })
        except Exception as e:
            st.error(f"AI analysis failed: {str(e)}")
            st.stop()

    # Metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Articles", len(news_results))
    c2.metric("Model", model_name)
    c3.metric("Temperature", temperature)
    c4.metric("Query", query[:20])

    st.divider()

    tab1, tab2, tab3 = st.tabs([
        "📊 Analysis",
        "📰 Articles",
        "🏷 Entities"
    ])

    # Analysis
    with tab1:
        st.subheader("Executive Summary")
        st.info(data.executive_summary)

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Top Headlines")
            for item in data.top_headlines:
                st.markdown(f"• {item}")

        with col2:
            st.subheader("Key Developments")
            for item in data.key_developments:
                st.markdown(f"• {item}")

        st.subheader("Impact Analysis")

        p1, p2 = st.columns(2)

        with p1:
            st.success("Positive Impact")
            for item in data.impact_analysis.positive:
                st.markdown(f"• {item}")

        with p2:
            st.error("Negative Impact")
            for item in data.impact_analysis.negative:
                st.markdown(f"• {item}")

        st.subheader("Risks")
        for item in data.risks:
            st.warning(item)

        st.subheader("Key Takeaways")
        for item in data.takeaways:
            st.markdown(f"✅ {item}")

    # Articles
    with tab2:
        for idx, article in enumerate(news_results, 1):
            with st.expander(f"Article {idx}"):
                st.write(article["content"])

    # Entities
    with tab3:
        st.subheader("Mentioned Entities")

        chips = "".join([
            f'<span class="entity-chip">{entity}</span>'
            for entity in data.entities
        ])

        st.markdown(chips, unsafe_allow_html=True)