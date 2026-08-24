from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go


# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="ChatGPT Digital DNA",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"


# ============================================================
# GLOBAL STYLE
# ============================================================

st.markdown(
    """
    <style>
    .stApp {
        background-color: #080b12;
    }

    [data-testid="stSidebar"] {
        background-color: #0d111a;
    }

    .block-container {
        max-width: 1400px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3 {
        color: #f5f7fb;
    }

    .hero-box {
        padding: 30px;
        border-radius: 20px;
        background: linear-gradient(
            135deg,
            rgba(99,91,255,0.20),
            rgba(0,198,255,0.08)
        );
        border: 1px solid rgba(255,255,255,0.10);
        margin-bottom: 25px;
    }

    .hero-title {
        font-size: 42px;
        font-weight: 800;
        color: #ffffff;
    }

    .hero-text {
        color: #aab3c5;
        font-size: 17px;
        line-height: 1.6;
    }

    .section-box {
        padding: 22px;
        border-radius: 18px;
        background: #101621;
        border: 1px solid #202938;
        margin-bottom: 15px;
    }

    .small-label {
        color: #8994a8;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .big-value {
        color: #ffffff;
        font-size: 30px;
        font-weight: 800;
    }

    .insight-box {
        padding: 20px;
        border-radius: 16px;
        background: #101621;
        border: 1px solid #202938;
        margin-bottom: 12px;
    }

    .insight-title {
        font-size: 18px;
        font-weight: 700;
        color: #ffffff;
    }

    .insight-text {
        color: #aab3c5;
        line-height: 1.6;
    }

    .share-box {
        padding: 35px;
        border-radius: 24px;
        background: linear-gradient(
            135deg,
            #121a2b,
            #0c1320
        );
        border: 1px solid #293750;
    }

    .share-title {
        font-size: 18px;
        font-weight: 700;
        letter-spacing: 1px;
    }

    .share-archetype {
        font-size: 48px;
        font-weight: 900;
        margin-top: 18px;
    }

    .share-description {
        color: #aab3c5;
        font-size: 16px;
        line-height: 1.7;
    }

    @media (max-width: 800px) {
        .hero-title {
            font-size: 32px;
        }

        .share-archetype {
            font-size: 36px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# DATA LOADING
# ============================================================

@st.cache_data
def load_csv(filename):
    path = OUTPUT_DIR / filename

    if not path.exists():
        return None

    try:
        return pd.read_csv(path)
    except Exception:
        return None


messages = load_csv("chat_messages.csv")
features = load_csv("conversation_features.csv")
behavior = load_csv("behavioral_patterns.csv")
dna_profile = load_csv("digital_dna_profile_v2.csv")
dna_scores = load_csv("conversation_dna_scores.csv")
topics = load_csv("conversation_topics_v4.csv")
stats = load_csv("conversation_stats.csv")


# ============================================================
# HELPERS
# ============================================================

def first_existing(df, columns):
    if df is None:
        return None

    for column in columns:
        if column in df.columns:
            return column

    return None


def number(value):
    try:
        if value is None or pd.isna(value):
            return "0"
        return f"{float(value):,.0f}"
    except Exception:
        return "0"


def decimal(value):
    try:
        if value is None or pd.isna(value):
            return "0.00"
        return f"{float(value):.2f}"
    except Exception:
        return "0.00"


def minutes(value):
    try:
        if value is None or pd.isna(value):
            return "0 min"

        value = float(value)

        if value < 60:
            return f"{value:.0f} min"

        hours = value / 60

        if hours < 24:
            return f"{hours:.1f} hrs"

        return f"{hours / 24:.1f} days"

    except Exception:
        return "0 min"


def clean_title(value):
    if value is None:
        return "Untitled conversation"

    value = str(value).strip()

    if not value:
        return "Untitled conversation"

    return value


# ============================================================
# DNA
# ============================================================

def get_dna_dataframe():

    if dna_profile is None:
        return pd.DataFrame(
            columns=["Trait", "Score"]
        )

    trait_column = first_existing(
        dna_profile,
        [
            "trait",
            "Trait",
            "dimension",
            "Dimension",
            "name",
            "Name",
        ],
    )

    score_column = first_existing(
        dna_profile,
        [
            "score",
            "Score",
            "value",
            "Value",
            "trait_score",
            "traitScore",
        ],
    )

    if trait_column and score_column:

        dna = dna_profile[
            [trait_column, score_column]
        ].copy()

        dna.columns = [
            "Trait",
            "Score",
        ]

    else:

        numeric = dna_profile.select_dtypes(
            include="number"
        )

        if numeric.empty:
            return pd.DataFrame(
                columns=["Trait", "Score"]
            )

        score_col = numeric.columns[0]

        dna = pd.DataFrame(
            {
                "Trait": dna_profile.index.astype(str),
                "Score": numeric[score_col].values,
            }
        )

    dna["Trait"] = (
        dna["Trait"]
        .astype(str)
        .str.strip()
    )

    dna["Score"] = pd.to_numeric(
        dna["Score"],
        errors="coerce",
    )

    dna = dna.dropna(
        subset=["Score"]
    )

    dna = dna[
        dna["Trait"].str.len() > 0
    ]

    return (
        dna.sort_values(
            "Score",
            ascending=False,
        )
        .reset_index(drop=True)
    )


# ============================================================
# ACTIVITY
# ============================================================

def get_activity_dataframe():

    if messages is None:
        return pd.DataFrame()

    df = messages.copy()

    if "datetime" in df.columns:

        df["datetime"] = pd.to_datetime(
            df["datetime"],
            errors="coerce",
        )

    elif "timestamp" in df.columns:

        timestamp_numeric = pd.to_numeric(
            df["timestamp"],
            errors="coerce",
        )

        df["datetime"] = pd.to_datetime(
            timestamp_numeric,
            unit="s",
            errors="coerce",
        )

    else:
        return pd.DataFrame()

    return df.dropna(
        subset=["datetime"]
    )


# ============================================================
# TOPICS
# ============================================================

def get_topic_counts():

    if topics is None:
        return pd.DataFrame(
            columns=[
                "Topic",
                "Conversations",
            ]
        )

    topic_column = first_existing(
        topics,
        [
            "topic",
            "Topic",
            "category",
            "Category",
        ],
    )

    if topic_column is None:
        return pd.DataFrame(
            columns=[
                "Topic",
                "Conversations",
            ]
        )

    counts = (
        topics[topic_column]
        .dropna()
        .astype(str)
        .str.strip()
        .value_counts()
        .reset_index()
    )

    counts.columns = [
        "Topic",
        "Conversations",
    ]

    return counts


# ============================================================
# BASIC METRICS
# ============================================================

def get_total_conversations():

    if features is not None:
        return len(features)

    if topics is not None:
        return len(topics)

    return 0


def get_total_messages():

    if messages is not None:
        return len(messages)

    if (
        features is not None
        and "total_messages" in features.columns
    ):

        values = pd.to_numeric(
            features["total_messages"],
            errors="coerce",
        )

        return values.sum()

    return 0


def get_average_messages():

    if (
        features is not None
        and "total_messages" in features.columns
    ):

        values = pd.to_numeric(
            features["total_messages"],
            errors="coerce",
        )

        return values.mean()

    return 0


def get_median_messages():

    if (
        features is not None
        and "total_messages" in features.columns
    ):

        values = pd.to_numeric(
            features["total_messages"],
            errors="coerce",
        )

        return values.median()

    return 0


# ============================================================
# TRAIT INTERPRETATION
# ============================================================

TRAIT_DESCRIPTIONS = {

    "builder":
        "Your conversations show a strong tendency toward creating, implementing, testing and iterating on ideas.",

    "learning":
        "Your activity contains a strong learning pattern, with repeated exploration, explanation and skill development.",

    "research":
        "Your conversations show a strong tendency to investigate topics, compare information and explore possibilities.",

    "creator":
        "Your activity shows a strong creative pattern involving ideas, content, projects and experimentation.",

    "troubleshooting":
        "Your conversations show a strong problem-solving pattern, especially around diagnosing issues and refining solutions.",

    "technical":
        "Your activity contains a strong technical signal across programming, tools, systems and implementation.",

    "persistence":
        "Your interaction history shows repeated iteration and continued engagement with problems instead of stopping early.",

    "iteration":
        "Your conversations demonstrate a tendency to repeatedly refine outputs until they reach the desired result.",
}


def normalize_trait_name(name):

    return (
        str(name)
        .lower()
        .strip()
        .replace("_", " ")
    )


def get_trait_description(trait):

    normalized = normalize_trait_name(trait)

    for key, description in TRAIT_DESCRIPTIONS.items():

        if key in normalized:
            return description

    return (
        "This dimension represents one of the strongest "
        "behavioral signals detected in your conversation data."
    )


# ============================================================
# GLOBAL DATA
# ============================================================

total_conversations = get_total_conversations()
total_messages = get_total_messages()
avg_messages = get_average_messages()
median_messages = get_median_messages()

dna = get_dna_dataframe()
topic_counts = get_topic_counts()

if not dna.empty:

    primary_trait = str(
        dna.iloc[0]["Trait"]
    )

    primary_score = float(
        dna.iloc[0]["Score"]
    )

else:

    primary_trait = "Builder"
    primary_score = 0.0


# ============================================================
# BEHAVIORAL INSIGHTS
# ============================================================

def get_behavioral_insights():

    insights = []

    if total_conversations > 0:

        insights.append(
            (
                "Conversation Explorer",
                f"You have analyzed {total_conversations:,} conversations, creating a substantial behavioral dataset.",
            )
        )

    if avg_messages >= 30:

        insights.append(
            (
                "Deep Interaction",
                f"Your average conversation contains {avg_messages:.1f} messages, suggesting that you often develop ideas through extended interaction.",
            )
        )

    elif avg_messages >= 15:

        insights.append(
            (
                "Iterative Thinker",
                f"With {avg_messages:.1f} messages per conversation on average, your activity shows meaningful iteration.",
            )
        )

    elif avg_messages > 0:

        insights.append(
            (
                "Rapid Explorer",
                f"Your average conversation length is {avg_messages:.1f} messages, indicating a tendency to explore many topics through shorter interactions.",
            )
        )

    if not topic_counts.empty:

        top_topic = str(
            topic_counts.iloc[0]["Topic"]
        )

        top_count = int(
            topic_counts.iloc[0]["Conversations"]
        )

        insights.append(
            (
                "Topic Signature",
                f"Your strongest conversation signal is '{top_topic}', appearing in approximately {top_count:,} conversations.",
            )
        )

    if (
        features is not None
        and "technical_term_count" in features.columns
    ):

        technical = pd.to_numeric(
            features["technical_term_count"],
            errors="coerce",
        ).dropna()

        if not technical.empty and technical.mean() > 0:

            insights.append(
                (
                    "Technical Builder",
                    "Your dataset contains measurable technical activity, suggesting that your ChatGPT usage frequently moves beyond simple information lookup.",
                )
            )

    if (
        features is not None
        and "max_user_message_length" in features.columns
    ):

        lengths = pd.to_numeric(
            features["max_user_message_length"],
            errors="coerce",
        ).dropna()

        if not lengths.empty and lengths.max() > 1000:

            insights.append(
                (
                    "High-Context Prompter",
                    f"Your longest recorded user message contains {lengths.max():,.0f} characters, indicating that you sometimes provide substantial context when solving problems.",
                )
            )

    if not insights:

        insights.append(
            (
                "Emerging Pattern",
                "More conversation data is needed to identify strong behavioral signals.",
            )
        )

    return insights


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("🧬 DIGITAL DNA")
st.sidebar.caption("ChatGPT Activity Intelligence")

page = st.sidebar.radio(
    "Explore",
    [
        "Command Center",
        "DNA Fingerprint",
        "Activity Evolution",
        "Topic Intelligence",
        "Behavior",
        "Deep Builds",
        "Your Profile",
        "Shareable DNA",
    ],
)

st.sidebar.divider()

st.sidebar.caption(
    "Python • Pandas • Plotly • Streamlit"
)


# ============================================================
# COMMAND CENTER
# ============================================================

if page == "Command Center":

    st.markdown(
        """
        <div class="hero-box">
            <div class="hero-title">
                🧬 ChatGPT Digital DNA
            </div>
            <div class="hero-text">
                A behavioral intelligence profile generated
                from your ChatGPT conversation history.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "CONVERSATIONS",
            number(total_conversations),
        )

    with c2:
        st.metric(
            "TOTAL MESSAGES",
            number(total_messages),
        )

    with c3:
        st.metric(
            "AVG / CONVERSATION",
            f"{avg_messages:.1f}",
        )

    with c4:
        st.metric(
            "MEDIAN / CONVERSATION",
            f"{median_messages:.0f}",
        )

    st.markdown("## 🧬 Your Digital DNA")

    with st.container(border=True):

        st.caption("PRIMARY ARCHETYPE")

        st.subheader(
            primary_trait.upper()
        )

        st.write(
            f"Strongest recorded behavioral dimension: "
            f"**{primary_score:.2f}**"
        )

        st.write(
            get_trait_description(
                primary_trait
            )
        )

    st.markdown("## 🧠 What Your Data Suggests")

    for title, description in get_behavioral_insights()[:5]:

        with st.container(border=True):

            st.subheader(
                f"🔎 {title}"
            )

            st.write(description)

    if not dna.empty:

        st.markdown(
            "## 🏆 Top Digital DNA Traits"
        )

        top_traits = dna.head(5)

        cols = st.columns(
            len(top_traits)
        )

        max_score = max(
            float(top_traits["Score"].max()),
            1,
        )

        for rank, (
            col,
            (_, row),
        ) in enumerate(
            zip(
                cols,
                top_traits.iterrows(),
            ),
            start=1,
        ):

            with col:

                score = float(
                    row["Score"]
                )

                st.metric(
                    f"#{rank} {row['Trait']}",
                    f"{score:.2f}",
                )

                st.progress(
                    min(
                        1.0,
                        score / max_score,
                    )
                )

    if len(dna) >= 3:

        st.markdown(
            "## 🧬 DNA Fingerprint"
        )

        radar = dna.head(10)

        traits = (
            radar["Trait"]
            .astype(str)
            .tolist()
        )

        scores = (
            radar["Score"]
            .astype(float)
            .tolist()
        )

        traits.append(traits[0])
        scores.append(scores[0])

        fig = go.Figure()

        fig.add_trace(
            go.Scatterpolar(
                r=scores,
                theta=traits,
                fill="toself",
                name="Digital DNA",
            )
        )

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            title="Your Behavioral DNA",
            polar=dict(
                bgcolor="rgba(0,0,0,0)",
                radialaxis=dict(
                    visible=True
                ),
            ),
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    st.markdown("## 🏆 Personal Records")

    r1, r2, r3 = st.columns(3)

    deepest_title = "N/A"
    deepest_messages = 0

    if (
        features is not None
        and "total_messages" in features.columns
        and not features.empty
    ):

        values = pd.to_numeric(
            features["total_messages"],
            errors="coerce",
        )

        if values.notna().any():

            index = values.idxmax()
            row = features.loc[index]

            deepest_title = clean_title(
                row.get(
                    "title",
                    "Untitled conversation",
                )
            )

            deepest_messages = values.loc[index]

    with r1:

        st.metric(
            "🔥 DEEPEST CONVERSATION",
            number(deepest_messages),
        )

        st.caption(
            deepest_title
        )

    technical_title = "N/A"
    technical_count = 0

    if (
        features is not None
        and "technical_term_count" in features.columns
        and not features.empty
    ):

        values = pd.to_numeric(
            features["technical_term_count"],
            errors="coerce",
        )

        if values.notna().any():

            index = values.idxmax()
            row = features.loc[index]

            technical_title = clean_title(
                row.get(
                    "title",
                    "Untitled conversation",
                )
            )

            technical_count = values.loc[index]

    with r2:

        st.metric(
            "🛠️ MOST TECHNICAL",
            number(technical_count),
        )

        st.caption(
            technical_title
        )

    longest_message = 0

    if (
        features is not None
        and "max_user_message_length" in features.columns
    ):

        values = pd.to_numeric(
            features["max_user_message_length"],
            errors="coerce",
        )

        if values.notna().any():

            longest_message = values.max()

    with r3:

        st.metric(
            "📝 LONGEST USER MESSAGE",
            number(longest_message),
        )

        st.caption(
            "characters"
        )

    if not topic_counts.empty:

        st.markdown(
            "## 🎯 Conversation Portfolio"
        )

        col1, col2 = st.columns(2)

        with col1:

            fig = px.pie(
                topic_counts,
                names="Topic",
                values="Conversations",
                hole=0.55,
                title="Topic Distribution",
            )

            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                height=450,
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

        with col2:

            fig = px.bar(
                topic_counts.sort_values(
                    "Conversations"
                ),
                x="Conversations",
                y="Topic",
                orientation="h",
                title="Topics Ranked",
            )

            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                height=450,
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

    activity = get_activity_dataframe()

    if not activity.empty:

        activity["month"] = (
            activity["datetime"]
            .dt.to_period("M")
            .astype(str)
        )

        monthly = (
            activity
            .groupby("month")
            .size()
            .reset_index(
                name="Messages"
            )
        )

        st.markdown(
            "## 📈 Activity Timeline"
        )

        fig = px.line(
            monthly,
            x="month",
            y="Messages",
            markers=True,
            title="Messages Over Time",
        )

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )


# ============================================================
# DNA FINGERPRINT
# ============================================================

elif page == "DNA Fingerprint":

    st.title("🧬 DNA Fingerprint")

    st.caption(
        "Your strongest behavioral dimensions across conversations."
    )

    if dna.empty:

        st.error(
            "No usable DNA scoring data was found."
        )

    else:

        top = dna.head(5)

        cols = st.columns(
            len(top)
        )

        for rank, (
            col,
            (_, row),
        ) in enumerate(
            zip(
                cols,
                top.iterrows(),
            ),
            start=1,
        ):

            with col:

                st.metric(
                    f"#{rank} {row['Trait']}",
                    f"{float(row['Score']):.2f}",
                )

        st.markdown(
            "## 🧠 Trait Interpretation"
        )

        for _, row in dna.head(5).iterrows():

            trait = str(row["Trait"])
            score = float(row["Score"])

            with st.container(border=True):

                st.subheader(
                    f"🧬 {trait}"
                )

                st.write(
                    f"Score: **{score:.2f}**"
                )

                st.write(
                    get_trait_description(trait)
                )

        if len(dna) >= 3:

            radar = dna.head(10)

            traits = (
                radar["Trait"]
                .astype(str)
                .tolist()
            )

            scores = (
                radar["Score"]
                .astype(float)
                .tolist()
            )

            traits.append(traits[0])
            scores.append(scores[0])

            fig = go.Figure()

            fig.add_trace(
                go.Scatterpolar(
                    r=scores,
                    theta=traits,
                    fill="toself",
                    name="Digital DNA",
                )
            )

            fig.update_layout(
                template="plotly_dark",
                title="Digital DNA Radar",
                polar=dict(
                    bgcolor="rgba(0,0,0,0)",
                    radialaxis=dict(
                        visible=True
                    ),
                ),
                paper_bgcolor="rgba(0,0,0,0)",
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

        fig = px.bar(
            dna.sort_values("Score"),
            x="Score",
            y="Trait",
            orientation="h",
            title="Trait Strength",
        )

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            height=520,
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )


# ============================================================
# ACTIVITY EVOLUTION
# ============================================================

elif page == "Activity Evolution":

    st.title("📈 Activity Evolution")

    st.caption(
        "How your ChatGPT usage changed over time."
    )

    df = get_activity_dataframe()

    if df.empty:

        st.error(
            "No valid timestamp data was found."
        )

    else:

        df["month"] = (
            df["datetime"]
            .dt.to_period("M")
            .astype(str)
        )

        monthly = (
            df.groupby("month")
            .size()
            .reset_index(
                name="Messages"
            )
        )

        fig = px.line(
            monthly,
            x="month",
            y="Messages",
            markers=True,
            title="Messages Over Time",
        )

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

        if "role" in df.columns:

            st.markdown(
                "## 💬 Interaction Balance"
            )

            role_counts = (
                df["role"]
                .value_counts()
                .reset_index()
            )

            role_counts.columns = [
                "Role",
                "Messages",
            ]

            fig = px.pie(
                role_counts,
                names="Role",
                values="Messages",
                hole=0.55,
                title="User vs Assistant Messages",
            )

            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

        df["hour"] = (
            df["datetime"].dt.hour
        )

        hourly = (
            df.groupby("hour")
            .size()
            .reset_index(
                name="Messages"
            )
        )

        fig = px.bar(
            hourly,
            x="hour",
            y="Messages",
            title="Hourly Activity Pattern",
        )

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

        st.markdown(
            "## 🔥 Activity Heatmap"
        )

        df["day"] = (
            df["datetime"]
            .dt.day_name()
        )

        day_order = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]

        heatmap = (
            df.groupby(
                ["day", "hour"]
            )
            .size()
            .reset_index(
                name="Messages"
            )
        )

        heatmap["day"] = pd.Categorical(
            heatmap["day"],
            categories=day_order,
            ordered=True,
        )

        heatmap = heatmap.sort_values(
            ["day", "hour"]
        )

        pivot = heatmap.pivot(
            index="hour",
            columns="day",
            values="Messages",
        ).fillna(0)

        pivot = pivot.reindex(
            columns=day_order
        )

        fig = px.imshow(
            pivot,
            labels={
                "x": "Day",
                "y": "Hour",
                "color": "Messages",
            },
            title="Messages by Day and Hour",
            aspect="auto",
        )

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )


# ============================================================
# TOPIC INTELLIGENCE
# ============================================================

elif page == "Topic Intelligence":

    st.title("🎯 Topic Intelligence")

    st.caption(
        "Your conversation portfolio according to Topic Classification V4."
    )

    counts = get_topic_counts()

    if counts.empty:

        st.error(
            "conversation_topics_v4.csv was not found "
            "or contains no topic column."
        )

    else:

        counts["Share"] = (
            counts["Conversations"]
            / counts["Conversations"].sum()
            * 100
        )

        col1, col2 = st.columns(2)

        with col1:

            fig = px.pie(
                counts,
                names="Topic",
                values="Conversations",
                hole=0.50,
                title="Topic Distribution",
            )

            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

        with col2:

            fig = px.bar(
                counts.sort_values(
                    "Conversations"
                ),
                x="Conversations",
                y="Topic",
                orientation="h",
                title="Topics Ranked",
            )

            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

        st.markdown(
            "## 🧠 Topic Signals"
        )

        for _, row in counts.head(5).iterrows():

            topic = str(row["Topic"])

            conversation_count = int(
                row["Conversations"]
            )

            share = float(
                row["Share"]
            )

            with st.container(border=True):

                st.subheader(
                    f"🎯 {topic}"
                )

                st.write(
                    f"Appears in **{conversation_count:,}** "
                    f"conversations, representing "
                    f"**{share:.1f}%** of classified conversations."
                )

        st.markdown(
            "## 📋 Complete Topic Data"
        )

        st.dataframe(
            counts,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# BEHAVIOR
# ============================================================

elif page == "Behavior":

    st.title("🧠 Behavioral Intelligence")

    st.caption(
        "How you interact, build and solve problems."
    )

    if behavior is None:

        st.error(
            "behavioral_patterns.csv was not found."
        )

    else:

        if "conversation_type" in behavior.columns:

            types = (
                behavior["conversation_type"]
                .dropna()
                .astype(str)
                .value_counts()
                .reset_index()
            )

            types.columns = [
                "Type",
                "Conversations",
            ]

            fig = px.bar(
                types.sort_values(
                    "Conversations"
                ),
                x="Conversations",
                y="Type",
                orientation="h",
                title="Conversation Archetypes",
            )

            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

        score_candidates = [
            "depth_score",
            "builder_score",
            "learning_score",
            "research_score",
            "creator_score",
            "troubleshooting_score",
            "persistence_score",
            "iteration_score",
            "technical_score",
        ]

        available = [
            column
            for column in score_candidates
            if column in behavior.columns
        ]

        if available:

            selected = st.selectbox(
                "Behavioral metric",
                available,
            )

            fig = px.histogram(
                behavior,
                x=selected,
                nbins=25,
                title=selected.replace(
                    "_",
                    " ",
                ).title(),
            )

            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

            numeric_values = pd.to_numeric(
                behavior[selected],
                errors="coerce",
            ).dropna()

            if not numeric_values.empty:

                st.markdown(
                    "## 📊 Behavioral Summary"
                )

                c1, c2, c3 = st.columns(3)

                with c1:
                    st.metric(
                        "AVERAGE",
                        f"{numeric_values.mean():.2f}",
                    )

                with c2:
                    st.metric(
                        "MEDIAN",
                        f"{numeric_values.median():.2f}",
                    )

                with c3:
                    st.metric(
                        "MAXIMUM",
                        f"{numeric_values.max():.2f}",
                    )

        else:

            st.info(
                "No individual behavioral score columns "
                "were found in behavioral_patterns.csv."
            )


# ============================================================
# DEEP BUILDS
# ============================================================

elif page == "Deep Builds":

    st.title("🔥 Deep Builds")

    st.caption(
        "The conversations where you invested the most interaction."
    )

    if features is None:

        st.error(
            "conversation_features.csv was not found."
        )

    elif "total_messages" not in features.columns:

        st.error(
            "total_messages column is missing."
        )

    else:

        df = features.copy()

        df["total_messages"] = pd.to_numeric(
            df["total_messages"],
            errors="coerce",
        )

        df = df.dropna(
            subset=["total_messages"]
        )

        top = (
            df.sort_values(
                "total_messages",
                ascending=False,
            )
            .head(15)
        )

        for _, row in top.head(5).iterrows():

            title = clean_title(
                row.get(
                    "title",
                    "Untitled conversation",
                )
            )

            total = row.get(
                "total_messages",
                0,
            )

            duration = row.get(
                "duration_minutes",
                0,
            )

            technical = row.get(
                "technical_term_count",
                0,
            )

            with st.container(border=True):

                st.subheader(
                    f"🔥 {title}"
                )

                a, b, c = st.columns(3)

                with a:
                    st.metric(
                        "Messages",
                        number(total),
                    )

                with b:
                    st.metric(
                        "Duration",
                        minutes(duration),
                    )

                with c:
                    st.metric(
                        "Technical Terms",
                        number(technical),
                    )

        title_column = (
            "title"
            if "title" in top.columns
            else None
        )

        if title_column:

            chart = top.sort_values(
                "total_messages"
            )

            fig = px.bar(
                chart,
                x="total_messages",
                y="title",
                orientation="h",
                title="Top Conversations by Message Count",
            )

            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                height=600,
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )


# ============================================================
# YOUR PROFILE
# ============================================================

elif page == "Your Profile":

    st.title("🔎 Your Digital Profile")

    st.caption(
        "An evidence-based interpretation of the metrics in your dataset."
    )

    with st.container(border=True):

        st.caption(
            "PRIMARY DIGITAL DNA"
        )

        st.header(
            primary_trait.upper()
        )

        st.write(
            f"Current strongest score: "
            f"**{primary_score:.2f}**"
        )

        st.write(
            get_trait_description(
                primary_trait
            )
        )

    st.markdown(
        "## 🧠 Behavioral Signals"
    )

    for title, description in get_behavioral_insights():

        with st.container(border=True):

            st.subheader(
                f"🔎 {title}"
            )

            st.write(description)

    if not dna.empty:

        st.markdown(
            "## 🧬 Your Strongest Traits"
        )

        for rank, (_, row) in enumerate(
            dna.head(5).iterrows(),
            start=1,
        ):

            trait = str(
                row["Trait"]
            )

            score = float(
                row["Score"]
            )

            with st.container(border=True):

                st.subheader(
                    f"#{rank} 🧬 {trait}"
                )

                st.write(
                    f"Recorded DNA score: **{score:.2f}**"
                )

                st.write(
                    get_trait_description(
                        trait
                    )
                )

    st.markdown(
        "## 📊 Dataset Summary"
    )

    st.write(
        f"""
        ### {primary_trait}

        Your dataset contains:

        - **{total_conversations:,} conversations**
        - **{total_messages:,} messages**
        - **{avg_messages:.1f} average messages per conversation**
        - **{median_messages:.0f} median messages per conversation**

        The dashboard describes measurable interaction
        patterns with ChatGPT rather than attempting to
        define your personality.

        Your Digital DNA is based on activity such as
        conversation depth, technical activity, behavioral
        scores, topics, projects and interaction patterns.
        """
    )

    if not topic_counts.empty:

        st.markdown(
            "## 🎯 Your Conversation Portfolio"
        )

        top_topic = topic_counts.iloc[0]

        with st.container(border=True):

            st.subheader(
                "🎯 Most Frequent Topic"
            )

            st.write(
                f"**{top_topic['Topic']}** appears in "
                f"**{int(top_topic['Conversations']):,}** "
                "conversations."
            )


# ============================================================
# SHAREABLE DNA
# ============================================================

elif page == "Shareable DNA":

    st.title("📸 Shareable Digital DNA")

    st.caption(
        "A clean summary card for your portfolio, LinkedIn or project demo."
    )

    if not dna.empty:

        dna_stack = (
            dna.head(5)["Trait"]
            .astype(str)
            .tolist()
        )

    else:

        dna_stack = [
            "Builder",
            "Learning",
            "Research",
            "Creator",
            "Troubleshooting",
        ]

    if not topic_counts.empty:

        top_topics = (
            topic_counts
            .head(3)["Topic"]
            .astype(str)
            .tolist()
        )

    else:

        top_topics = [
            "Data Analytics",
            "Programming",
            "AI",
        ]

    st.markdown(
        """
        <div class="share-box">
            <div class="share-title">
                🧬 CHATGPT DIGITAL DNA
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"# {primary_trait.upper()}"
    )

    st.write(
        "A personal analytics project built from "
        "ChatGPT conversation history."
    )

    s1, s2, s3 = st.columns(3)

    with s1:
        st.metric(
            "CONVERSATIONS",
            number(total_conversations),
        )

    with s2:
        st.metric(
            "MESSAGES",
            number(total_messages),
        )

    with s3:
        st.metric(
            "DNA SCORE",
            f"{primary_score:.2f}",
        )

    st.markdown(
        "### 🧬 DNA Stack"
    )

    st.write(
        " • ".join(dna_stack)
    )

    st.markdown(
        "### 🎯 Top Conversation Signals"
    )

    st.write(
        ", ".join(top_topics)
    )

    st.caption(
        "Personal Analytics Project • Python • Pandas • Plotly • Streamlit"
    )

    st.info(
        "📸 Use your browser screenshot tool to capture "
        "this section for your portfolio or LinkedIn."
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "🧬 ChatGPT Digital DNA V6 • Personal Analytics Project"
)