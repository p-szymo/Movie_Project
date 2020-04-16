# Function to grab a set of unique genres from the 'genres' column in the dataframe.
def unique_genres(data):
    genre_list = []
    for listing in data:
        for element in listing:
            genre_list.append(element)
    return list(set(genre_list))