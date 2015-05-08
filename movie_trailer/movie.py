#!/usr/bin/env python
#
# Author: Ying Xiong.
# Created: May 08, 2015.

from fresh_tomatoes import open_movies_page

class Movie:
    """A movie object that contains information about its title, box art and
    youtube trailer.."""

    def __init__(self, title, poster_image_url, trailer_youtube_url):
        """Create an object with corrsponding information supplied as input."""
        self.title = title
        self.poster_image_url = poster_image_url
        self.trailer_youtube_url = trailer_youtube_url

# Create a list of favorite movies together with their box arts (from Wikipedia)
# and Youtube trailers.
favorite_movies = [
    Movie("Forrest Gump",
          "https://upload.wikimedia.org/wikipedia/en/6/67/Forrest_Gump_poster.jpg",
          "https://www.youtube.com/watch?v=bLvqoHBptjg"),
    Movie("Schindler's List",
          "https://upload.wikimedia.org/wikipedia/en/3/38/Schindler%27s_List_movie.jpg",
          "https://www.youtube.com/watch?v=_cH8w0Cl_-k"),
    Movie("Shawshank Redemption",
          "https://upload.wikimedia.org/wikipedia/en/8/81/ShawshankRedemptionMoviePoster.jpg",
          "https://www.youtube.com/watch?v=K_tLp7T6U1c"),
    Movie("The Incredibles",
          "https://upload.wikimedia.org/wikipedia/en/e/ec/The_Incredibles.jpg",
          "https://www.youtube.com/watch?v=sZwWCrFNfzQ"),
    Movie("Mosters, Inc.",
          "https://upload.wikimedia.org/wikipedia/en/6/63/Monsters_Inc.JPG",
          "https://www.youtube.com/watch?v=8IBNZ6O2kMk"),
    Movie("The Lion King",
          "https://upload.wikimedia.org/wikipedia/en/3/3d/The_Lion_King_poster.jpg",
          "https://www.youtube.com/watch?v=MPugv1k7r-s"),
    Movie("Titanic",
          "https://upload.wikimedia.org/wikipedia/en/2/22/Titanic_poster.jpg",
          "https://www.youtube.com/watch?v=2e-eXJ6HgkQ"),
    Movie("Lord of the Rings",
          "https://upload.wikimedia.org/wikipedia/en/8/87/Ringstrilogyposter.jpg",
          "https://www.youtube.com/watch?v=Pki6jbSbXIY"),
    Movie("Gone with the Wind",
          "https://upload.wikimedia.org/wikipedia/commons/thumb/2/27/Poster_-_Gone_With_the_Wind_01.jpg/1024px-Poster_-_Gone_With_the_Wind_01.jpg",
          "https://www.youtube.com/watch?v=6T9THgvzaW0"),
]

if __name__ == "__main__":
    # Generate the webpage with the provided helper function.
    open_movies_page(favorite_movies)
