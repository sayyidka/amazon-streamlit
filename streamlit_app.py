from pprint import pprint

import streamlit as st
import altair as alt
import plotly.express as px
import plotly.figure_factory as ff
import psycopg2
import pandas as pd

# Set layout
st.set_page_config(layout="centered")

# Initialize connection.
# Uses st.cache to only run once.
@st.cache(allow_output_mutation=True, hash_funcs={"_thread.RLock": lambda _: None})
def init_connection():
    return psycopg2.connect(**st.secrets["postgres"])


conn = init_connection()

# Perform query.
# Uses st.cache to only rerun when the query changes or after 10 min.
@st.cache(ttl=600)
def run_query(query):
    with conn.cursor() as cur:
        cur.execute(query)
        colnames = [desc[0] for desc in cur.description]
        return (colnames, cur.fetchall())


data = run_query("SELECT * from books;")
headers = data[0]  # DB columns names
raw_data = data[1]  # DB query result
df = pd.DataFrame(raw_data, columns=headers)

# Titles
st.title("Amazon latest books")
st.header("Here are insights about latest 50 books released on Amazon in France :")

# Images
images_query = run_query("SELECT image FROM books")
images = [img[0] for img in images_query[1]]
st.image(images, width=50)

# Raw data
st.subheader("Raw data")
st.dataframe(df)

# Price
st.subheader("Prices (€)")
average_price_query = run_query("SELECT ROUND(AVG(price)) from books")
average_price = average_price_query[1][0][0]
st.metric(label="Average price", value=f"{str(average_price)} €")

st.write("All prices")
prices_query = run_query("SELECT title, price FROM books ORDER BY price")
chart_prices = pd.DataFrame(prices_query[1], columns=prices_query[0], dtype=str)
p = (
    alt.Chart(chart_prices, height=700)
    .mark_bar(color="orange", size=5)
    .encode(x=alt.X("title:N"), y=alt.Y("price:Q", sort="-y"))
)
st.altair_chart(p, use_container_width=True)

# Rating
st.subheader("Rating")
average_rating_query = run_query("SELECT ROUND(AVG(rating)) from books")
average_rating = average_rating_query[1][0][0]
st.metric(label="Average rating", value=f"{str(average_rating)} stars")

st.write("All ratings")
rating_query = run_query("SELECT * FROM books WHERE rating IS NOT NULL ORDER BY rating")
chart_ratings = pd.DataFrame(rating_query[1], columns=rating_query[0], dtype=str)
r = (
    alt.Chart(chart_ratings, height=500)
    .mark_circle(size=60)
    .encode(x="title:N", y="rating:Q", tooltip=["title", "author", "rating"])
    .interactive()
)
st.altair_chart(r, use_container_width=True)

# Comments
st.subheader("Comments")
average_comments_query = run_query("SELECT ROUND(AVG(comments)) FROM books")
average_comments = average_comments_query[1][0][0]
st.metric(label="Average number of comments", value=f"{str(average_comments)}")

most_commented_query = run_query(
    "SELECT title FROM books ORDER BY comments DESC LIMIT 1"
)
most_commented = most_commented_query[1][0][0]
st.metric(label="Most commented book", value=f"{str(most_commented)}")

# Book format
st.subheader("Format")
format_query = run_query("SELECT format, COUNT(format) FROM books GROUP BY format")
format_df = pd.DataFrame(format_query[1], columns=format_query[0], dtype=str)
fig = px.pie(
    format_df,
    values="count",
    names="format",
    color_discrete_sequence=px.colors.qualitative.Vivid,
)
st.plotly_chart(fig, use_container_width=True)
