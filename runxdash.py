import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
import calendar
import datetime
import pytz
import requests
from streamlit_agraph import agraph, Node, Edge, Config

from dataset_columns import COLUMNS

AVAILABLE_METRICS = [
    COLUMNS.impressions,
    COLUMNS.engagements,
    COLUMNS.likes,
    COLUMNS.replies,
    COLUMNS.retweets,
    COLUMNS.user_profile_clicks,
    COLUMNS.media_views,
]

COMMENT_METRICS = [
    COLUMNS.impressions,
    COLUMNS.engagements,
    COLUMNS.likes,
    COLUMNS.replies,
    COLUMNS.user_profile_clicks,
]



#%%%%%%%%%%%%%%%%%%%%%%#%%%%%%%%%%%%%%%%%%%%%%#%%%%%%%%%%%%%%%%%%%%%%

# --- UTILITY FUNCTIONS ---
        
# --- Preprocessing functions ---
def remove_outliers_iqr(data, column_name):
    Q1 = data[column_name].quantile(0.25)
    Q3 = data[column_name].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    data_no_outliers = data[(data[column_name] >= lower_bound) & (data[column_name] <= upper_bound)]
    return data_no_outliers

def preprocess(dataset):
    # Sort the dataset by 'time' column in descending order
    dataset = dataset.sort_values(by=COLUMNS.impressions, ascending=False)
    
    # Drop duplicates in 'Tweet id' column, keeping the first occurrence (highest value)
    dataset = dataset.drop_duplicates(subset=COLUMNS.tweet_id, keep='first')
    
    # Remove duplicates and handle missing values if needed
    tweet_text = dataset[COLUMNS.tweet_text].fillna("")
    comment_mask = tweet_text.str.startswith('@')
    comment_df = dataset[comment_mask]
    post_df = dataset[~comment_mask]

    dataset[COLUMNS.time] = pd.to_datetime(dataset[COLUMNS.time])
    post_df[COLUMNS.time] = pd.to_datetime(post_df[COLUMNS.time])
    comment_df[COLUMNS.time] = pd.to_datetime(comment_df[COLUMNS.time])
    
    return dataset, post_df, comment_df
    
# --- End of Preprocessing ---
# --- Performance Comparison ---
def pick_timeframes(all_df):
    st.subheader("How Has Your :blue[Performance] Changed?", divider='rainbow')
    st.markdown("Select ANY two :blue[Timeframes] to see a comparison of your performance. The resulting percentages will show your performance during the :blue[**first timeframe relative to the second**].")
    time_values = pd.to_datetime(all_df[COLUMNS.time])
    min_date_allowed = time_values.min()
    max_date_allowed = time_values.max()

    # Midpoint of the available date range
    midpoint_date = min_date_allowed + (max_date_allowed - min_date_allowed) / 2

    start_date1 = midpoint_date.date()#pd.to_datetime(df['time']).min().to_pydatetime().date() 
    end_date1 = max_date_allowed.date()
    
    timeframe1 = st.date_input("Pick the first timeframe", value=[start_date1, end_date1], 
                  min_value=min_date_allowed, max_value=max_date_allowed)

    start_date2 = min_date_allowed.date() 
    # `end_date2` should start 1 day before the `midpoint_date`
    end_date2 = (midpoint_date - pd.Timedelta(days=1)).date()#pd.to_datetime(df['time']).max().to_pydatetime().date()
    
    timeframe2 = st.date_input("Pick the second timeframe", value=[start_date2, end_date2], 
                  min_value=min_date_allowed, max_value=max_date_allowed)



    return timeframe1, timeframe2
    
def performance_comparison(all_df, posts, comments, available_metrics, timeframe1, timeframe2):

    # Access start and end dates 
    date1_start, date1_end = timeframe1
    date2_start, date2_end = timeframe2
    
    # All data
    df_date1 = all_df[(all_df[COLUMNS.time].dt.date >= date1_start) & (all_df[COLUMNS.time].dt.date <= date1_end)]
    df_date2 = all_df[(all_df[COLUMNS.time].dt.date >= date2_start) & (all_df[COLUMNS.time].dt.date <= date2_end)]

    # Posts data
    posts_date1 = posts[(posts[COLUMNS.time].dt.date >= date1_start) & (posts[COLUMNS.time].dt.date <= date1_end)]
    posts_date2 = posts[(posts[COLUMNS.time].dt.date >= date2_start) & (posts[COLUMNS.time].dt.date <= date2_end)]

    # Comments data
    comments_date1 = comments[(comments[COLUMNS.time].dt.date >= date1_start) & (comments[COLUMNS.time].dt.date <= date1_end)]
    comments_date2 = comments[(comments[COLUMNS.time].dt.date >= date2_start) & (comments[COLUMNS.time].dt.date <= date2_end)]

    # Form Performance Comparison DataFrame
    performance_comparison_data = []

    # Comments count
    num_comments_date1 = comments_date1[COLUMNS.tweet_text].count()
    num_comments_date2 = comments_date2[COLUMNS.tweet_text].count()

    # Num of Posts
    num_posts_date1 = posts_date1[COLUMNS.tweet_text].count()
    num_posts_date2 = posts_date2[COLUMNS.tweet_text].count()

    
    # Work out the changes
    comments_change = round(((num_comments_date1 - num_comments_date2)/num_comments_date2*100), 2)
    posts_change = round(((num_posts_date1 - num_posts_date2)/num_posts_date2*100), 2)
    
    performance_comparison_data.append({'Metric': 'Posts', 'Current': num_posts_date1,'Change': posts_change})
    performance_comparison_data.append({'Metric': 'Comments', 'Current': num_comments_date1, 'Change': comments_change})
    
    for metric in available_metrics:
        metric_in_date1_range = df_date1[metric].sum()
        metric_in_date2_range = df_date2[metric].sum()
        change = round(((metric_in_date1_range - metric_in_date2_range)/metric_in_date2_range*100), 2)
        performance_comparison_data.append({'Metric': metric.capitalize(), 
                                            'Current':metric_in_date1_range,'Change': change})

    
    data_frame = pd.DataFrame(performance_comparison_data)

    # Display the metric current value and change in %
    i = 0
    while i < len(data_frame):
        col1, col2, col3 = st.columns(3)
        col1.metric(data_frame.iloc[i, 0], data_frame.iloc[i, 1], data_frame.iloc[i, 2])
        i += 1
        col2.metric(data_frame.iloc[i, 0], data_frame.iloc[i, 1], data_frame.iloc[i, 2])
        i += 1
        col3.metric(data_frame.iloc[i, 0], data_frame.iloc[i, 1], data_frame.iloc[i, 2])
        i += 1

    # Display in a table
    st.divider()
    st.subheader("Table of results", divider='rainbow')
    #st.divider()
    df_table = pd.DataFrame(
        {
            "metric": data_frame['Metric'],
            #"current": data_frame['Current'],
            "change": data_frame['Change'],  
        }
    )
        
    st.dataframe(
        df_table,
        column_config={
            "metric": st.column_config.TextColumn("Metric"),
            #"current": st.column_config.TextColumn("Current"),
            "change": st.column_config.TextColumn("Change in %"),
        },
        hide_index=True,
        use_container_width=True,
    )


    
# --- Time Analysis --- 
def time_analysis(data_for_time_analysis, tz_selector):
    time_group = pd.to_datetime(data_for_time_analysis[COLUMNS.time]).dt.hour
    metrics = [COLUMNS.impressions, COLUMNS.engagements, COLUMNS.user_profile_clicks]
    time_by_impressions = data_for_time_analysis.groupby(time_group)[metrics].mean()
    

    ############
    # Plot the best days of the week
    average_chart = pd.DataFrame(
       {
           "Hour": time_by_impressions.index,
           "Impressions": time_by_impressions[COLUMNS.impressions].round(2),
           "Engagements": time_by_impressions[COLUMNS.engagements].round(2),
           "Profile Visits": time_by_impressions[COLUMNS.user_profile_clicks].round(2),
       }
    )

    st.bar_chart(average_chart.set_index('Hour'), color=["#76ECF0", "#F076C0", "#189599"]) 
    
# --- End of Time Analysis ---
# --- best_times_to_post ---
def best_times_to_post(data, metric_selector, tz_selector):
    # Convert `time` to the user-selected timezone
    time_series = pd.to_datetime(data[COLUMNS.time], errors='coerce')
    timezone = pytz.timezone(tz_selector)
    try:
        time_series = time_series.dt.tz_localize('UTC')
    except TypeError:
        # Already timezone-aware
        pass
    time_series = time_series.dt.tz_convert(timezone)

    time_of_day_avg = data.groupby(time_series.dt.hour)[metric_selector].mean()
    day_of_week_avg = data.groupby(time_series.dt.dayofweek)[metric_selector].mean()

    #st.header('Best :blue[Times/Days] To Post:sunglasses:')
    
    # Plot the best times of the day
    time_of_day_chart = pd.DataFrame(
       {
           "Hour": time_of_day_avg.index,
           metric_selector.capitalize(): time_of_day_avg.round(2),
       }
    )
    st.bar_chart(time_of_day_chart, x="Hour", y=metric_selector.capitalize())#, color="col3")

    # Plot the best days of the week
    day_of_week_chart = pd.DataFrame(
       {
           "Day": day_of_week_avg.index,
           metric_selector.capitalize(): day_of_week_avg.round(2),
       }
    )
    # Convert numerical day index to day names
    day_of_week_chart['Day'] = day_of_week_chart['Day'].apply(lambda x: calendar.day_name[x])
    st.bar_chart(day_of_week_chart, x="Day", y=metric_selector.capitalize(), color="#48DCC8")

# --- End of Time best_times_to_post Function
# --- Content Analysis Function ---
# Function to format the hover information
def show_posts(data):

    df = pd.DataFrame(
        {
            "post": data[COLUMNS.post_text],
            "impressions": data[COLUMNS.post_impressions],
            "replies": data[COLUMNS.post_replies],
            "profile_clicks": data[COLUMNS.post_profile_visits],
            "likes": data[COLUMNS.post_likes],
            "retweets": data[COLUMNS.post_reposts],
            "link": data[COLUMNS.post_link],
        }
    )

    
    st.dataframe(
        df,
        column_config={
            "post": st.column_config.TextColumn(
                "Posts",
                #help="Streamlit **widget** commands 🎈",
                max_chars=60,
            ),
            "impressions": st.column_config.NumberColumn(
                "Impressions",
                #help="Number of stars on GitHub",
                format="%d 👁️",
            ),
            "replies": st.column_config.NumberColumn(
                "Replies",
                #help="Number of stars on GitHub",
                format="%d ✍️",
            ),
            "profile_clicks": st.column_config.NumberColumn(
                "Reposts",
                #help="Number of stars on GitHub",
                format="%d 🧲",
            ),
            "likes": st.column_config.NumberColumn(
                "Likes",
                #help="Number of stars on GitHub",
                format="%d 🫶",
            ),
            "retweets": st.column_config.NumberColumn(
                "Reposts",
                #help="Number of stars on GitHub",
                format="%d 🔁",
            ),
            "link": st.column_config.LinkColumn("Link", help="Double click on the link."),
        },
        hide_index=True,
    )
    
def show_top_comments(sorted_df):
        
    df = pd.DataFrame(
        {
            "comment": sorted_df[COLUMNS.tweet_text],
            "link": sorted_df[COLUMNS.tweet_permalink],
        }
    )
    
    st.dataframe(
        df,
        column_config={
            "comment": st.column_config.TextColumn(
                "Comment",
                max_chars=60,
            ),
            "link": st.column_config.LinkColumn("Link", help="Double click on the link."),
        },
        hide_index=True,
    )

# --- End of Content Analysis Function ---
# --- Interacted Accounts Analysis Function ---
def show_top_accounts_in_circle(metric_selector, comment_df):
    comment_text = comment_df[COLUMNS.tweet_text].fillna("")
    # Extract the usernames user has mentioned
    mentioned_usernames_data = comment_text.str.extractall(r'@(\w+)')[0].unique().tolist()

    url_prefix = 'https://x.com/'

    # Calculate Total Metric for each username
    accounts_metric_data = []
    for username in mentioned_usernames_data:
        username_mask = comment_text.str.contains(username, regex=False)
        total_metric = comment_df.loc[username_mask, metric_selector].sum()
        mention_count = comment_df.loc[username_mask, metric_selector].count()
        accounts_metric_data.append({'Username': username, 'Total Metric': total_metric, 'Mention Count': mention_count})

    most_engaged_accounts = pd.DataFrame(accounts_metric_data).sort_values(by='Total Metric', ascending=False)


    # Round or Table radio buttons
    representation = st.radio("Representation", ["Table", "Graph"])

    # Graph representation
    if representation == "Graph":
        show_graph_circle(most_engaged_accounts)
    if representation == "Table":
        most_engaged_accounts['link'] = most_engaged_accounts['Username'].apply(create_hyperlink)
        # Simple table representation of accounts
        df = pd.DataFrame(
            {
                "username": most_engaged_accounts['link'],
                "total": most_engaged_accounts['Total Metric'],
                "mention_count": most_engaged_accounts['Mention Count'],
            }
        )
        
        st.dataframe(
            df,
            column_config={
                "username": st.column_config.LinkColumn(
                    "Username",
                    max_chars=60,
                ),
                "total": st.column_config.TextColumn("Total " + metric_selector),
                "mention_count": st.column_config.TextColumn("Mention Count"),
            },
            hide_index=True,
            use_container_width=True,
        )
# Function to create the hyperlink
def create_hyperlink(username):
    return f'https://twitter.com/{username}'

def show_graph_circle(accounts):

    url_prefix = 'https://unavatar.io/twitter/'
    #for row in accounts.iloc():

    nodes = []
    edges = []
    nodes.append( Node(id="You", 
                       label="", 
                       size=30, 
                       shape="circularImage",
                       image="http://cognimachina.com/wp-content/uploads/2023/11/F1x5VdQX0AA9Sgt.jpeg") 
                ) # includes **kwargs

    for i, row in enumerate(accounts.iloc):
        if i < 16:
            username = row.iloc[0]
            nodes.append( Node(id=username, 
                               size=35,
                               shape="circularImage",
                               image=f'{url_prefix}{username}') 
                        )
            edges.append( Edge(source="You", 
                               label="", 
                               target=username, 
                               # **kwargs
                               ) 
                        ) 
        else:
            break
        
    config = Config(width=750,
                    height=450,
                    directed=True, 
                    physics=True, 
                    hierarchical=True,
                    # **kwargs
                    )
    
    return_value = agraph(nodes=nodes, 
                          edges=edges, 
                          config=config)


# --- End of Interacted Accounts Analysis Function ---
###########################################




def run_xdash():#username):
    # Keep uploads scoped to a single browser session
    if "upload_cleanup_done" not in st.session_state:
        if os.path.exists("source_data.csv"):
            os.remove("source_data.csv")
        st.session_state["upload_cleanup_done"] = True

    df = st.session_state.get("uploaded_df")

    # Design the navigation bar
    with st.sidebar:  
        # st.image("https://images.rawpixel.com/image_800/cHJpdmF0ZS9sci9pbWFnZXMvd2Vic2l0ZS8yMDIyLTA1L3BmLXMxMjQtYWstMjYxNV8yLmpwZw.jpg")
        st.title(f"Welcome:wave:") #{username}
        choice = st.radio("Navigation", ["Upload", "Time Analysis", "Posts Summary", "Top Comments", "My Golden Connections", "Performance Comparison"])
        st.divider()
        st.info("This app allows you to see a kickass personalized report of your 𝕏 data. Choose 'Upload' to upload your data and start exploring!")
        st.subheader("", divider='gray')
        x_url = "https://x.com/CogniStark"
        feedback_form_url = "https://forms.gle/LeTggfuEBw9mBBGn8"
        st.markdown("by [@NickoStark](%s)"%x_url)
        st.markdown("Tell me about your experience with :red[𝕏]Dash [here](%s)"%feedback_form_url)
        

    if choice == "Upload":
        st.title("Personalized :red[𝕏]Dash")
        #st.title("Upload your 𝕏 data for Analysis")
        dataset = st.file_uploader("Upload your csv data here to get started.")
        if dataset:
            df = pd.read_csv(dataset, index_col=None)
            st.session_state["uploaded_df"] = df
            st.dataframe(df)

    data_not_found = 1
    if df is not None:
        data_not_found = 0
    
        # Clean the data
        #no_outlier = remove_outliers_iqr(df, COLUMNS.impressions)
        all_data, post_df, comment_df = preprocess(df)
        available_metrics = AVAILABLE_METRICS
        timezones = pytz.all_timezones
        
        # Default Timezone in the dataset
        default_timezone = 'UTC'
    
    
        
    #%%%%%%%%%%%%%%%%%%%%%% CHOICE 1
    if data_not_found == 1:
        st.warning("Upload your data, then we'll get to the analytics.")
    elif choice == "Time Analysis":
        st.markdown("<h1 style='text-align: center; color: white;'>Time Analysis</h1>", unsafe_allow_html=True)
        st.warning(
            "The latest X Analytics CSV export no longer includes the original timestamp column—"
            "only the calendar date is provided. Because the heatmaps and charts in this tab rely "
            "on hour-level data, we're keeping the Time Analysis tab off until the platform restores"
            "the timestamps."
        )

    #%%%%%%%%%%%%%%%%%%%%%% CHOICE 2
    elif choice == "Posts Summary":
        st.title("Posts Summary")
        st.info('''🔘 :green[SORT Posts:] Click on any column header to arrange posts based on the displayed metric.
                \n🔘 :green[Download, Search, Fullscreen:] Hover over the table to find icons for CSV download,
                search, and fullscreen mode.
                \n🔘 :green[Navigate to Posts:] Easily jump to a post by double-clicking on the link to make it clickable. 
        ''')
        st.subheader("", divider='gray')
        show_posts(post_df)
    
    #%%%%%%%%%%%%%%%%%%%%%% CHOICE 3
    elif choice == "Top Comments":
        st.title("Top Comments")
        st.subheader("Sometimes :green[Comments] Are Golder Than Posts, Ain't They?", divider='rainbow')
        
        # Add an expander for QXTips
        with st.expander("Actionable Tips"):
            st.markdown("1. You can double click/tap the :blue[links] to see, click and go to the comment.")
            st.markdown("2. Read your top comments again, categorize them and see :green[what type of comment gains more engagements].")
            st.markdown("3. Go over the accounts who have replied to those comments and interact with their posts.")
            st.markdown("4. Make your best comments into posts and publish them at the times provided in the :blue[Time Analysis]")
            st.markdown("5. Go to your comments, click on :green[Show Similar Posts], interact with the content similar to them. Add their authors to a :green[list] and keep on interacting with them.")
            st.markdown("6. You can go further and host or co-host a space around the topics that have gained a lot of interest.")
            
        
        metric_selector = st.selectbox("Choose a Metric", COMMENT_METRICS)
    
        # Widget for user-defined `n_top_posts`
        n_top_comments = st.number_input("Insert the number of top comments you'd like to see", value=None, step=1, placeholder="Type a number...")
        button_clicked = st.button("Show Comments")
        if button_clicked:
            if n_top_comments == None:
                st.warning('First tell me how many to show', icon="🤔")
            else:
                sorted_df = comment_df.sort_values(metric_selector, ascending=False).head(n_top_comments)
                st.subheader(f"Your {n_top_comments} top comments based on :green[{metric_selector.capitalize()}]:")
                show_top_comments(sorted_df)
    
    #%%%%%%%%%%%%%%%%%%%%%% CHOICE 4
    elif choice == "My Golden Connections":
        st.title("My Golden Connections")
        # Add an expander for QXTips
        with st.expander("Actionable Tips"):
            st.markdown("1. The accounts you've interacted with will be sorted based on the :blue[metric] you choose.")
            st.markdown("2. Accounts sorted based on :green[user profile clicks] are the ones that have brought you the :green[highest] traffic.")
            st.markdown("3. Add the top accounts to a :blue[list], turn on the :bell:, comment on their posts as soon as they publish")
        
        metric_selector = st.selectbox("Choose a Metric", COMMENT_METRICS)
    
        show_top_accounts_in_circle(metric_selector, comment_df)
    
    
    #%%%%%%%%%%%%%%%%%%%%%% CHOICE 5
    elif choice == "Performance Comparison":
        st.title("Performance Comparison")
    
        timeframe1, timeframe2 = pick_timeframes(all_data)
    
        button_clicked = st.button("Show Me How I did!")
        if button_clicked:
            performance_comparison(all_data, post_df, comment_df, available_metrics, timeframe1, timeframe2)
