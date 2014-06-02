#!/usr/bin/env python
import argparse
import imdb
from pyzipcode import ZipCodeDatabase
import yaml
import re


class Movie:
    """ Class that represents a movie"""

    def __init__(self):
        """Default constructo """

        self.id = None
        self.name = None
        self.imdbName = None
        self.year = None
        self.director = None
        self.cast = None
        self.genre = None
        self.imdbRating = None


    def getExtraInfo(self):
        """Get additiong information from IMDB"""

        imdbObj = imdb.IMDb()
        imdbMovieObj = imdbObj.search_movie(self.imdbName)[0]
        if imdbMovieObj['long imdb canonical title'] == self.imdbName:
            imdbID = imdbMovieObj.getID()
            imdbMovieObj = imdbObj.get_movie(imdbID)

            self.name = imdbMovieObj['title']
            self.year = imdbMovieObj['year']
            self.director = imdbMovieObj['director'][0]['name']
            # Gets the main 3 actors
            self.case = list(map((lambda x: x['name']), imdbMovieObj['cast'][:3]))
            self.ibdbRating = imdbMovieObj['rating']
        else:
            print("Warning: movie %s was not found on IMDB." % self.imdbName)
        

def parse_arguments():
    """ Function that parse main command line parameters

    Returns:
        * ok: argparse object
        * fail: argparse will exit
    """
    argParser = argparse.ArgumentParser(
        description='Proprocess tool for Movie Analysis')
    argParser.add_argument('config', help='Config file')
    argParser.add_argument('section',  help='Config file')

    args = argParser.parse_args()

    return args


def readYaml(filename):
    """
    Open a yaml config file

    returns:
        * ok: yaml dictionary
        * Fail: None
    """
    try:
        from yaml import CLoader as Loader, CDumper as Dumper
    except ImportError:
        from yaml import Loader, Dumper
    
    # Open the File
    try:
        fh = open(filename, 'r')
    except:
        return None

    yamlFile = yaml.load(fh)
    fh.close()
    
    return yamlFile



def read_csv_from_file(filename, sep=",", eol="\n"):
    """Return a generator with all the content of a column in a file"""

    try:
        fh = open(filename, 'r')
    except:
        yield None

    if fh: 
        # Remove EOL
        remove_eol = re.compile(eol + '$') 
        for line in fh:
            line = re.sub(remove_eol, "", line)
            columns = line.split(sep)
    
            yield columns
    
        fh.close()


def get_extra_info_from_movies(moviesDict):
    """Get additional info from the input movies files.

    The input is a dictionary of Movie object.
    """
    # XXX: limited to 10 rows just for testing
    for movieObj in list(moviesDict.values())[:5]:
        movieObj.getExtraInfo()


def load_movies(filename):
    """Return a dictionary of movies objects given a movies input file"""

    moviesGen = read_csv_from_file(filename,  sep='::')
    if not moviesGen:
        print("Error reading movies file")
        return None
    
    ret = {}
    # Iterate over all the file
    for line in moviesGen:
        (movieID, name, genres) = line
        if name not in ret:
            # The movie is not in the dictionary. Lets add it
            # 1st Construct the Movie Obj
            movie = Movie()
            movie.id = movieID
            movie.imdbName = name
            movie.genre = genres.split('|')
            
            # 2nd Add it to the return dict
            ret[movie.imdbName] = movie

    return ret
    


def main():
    cmdArgs = parse_arguments()
    config = readYaml(cmdArgs.config)
    if not config:
        print("Error loading the config file %s" % cmdArgs.config)
        return 1
    if cmdArgs.section not in config:
        print("Section %s does not exist" % cmdArgs.section)
        return 1


    config = config[cmdArgs.section]
    movieFile = "%s/%s" %   \
      (config['input']['base_path'], config['input']['movie'])

    # Load all movies
    moviesDict = load_movies(movieFile)

    # get extra info from IMDB    
    get_extra_info_from_movies(moviesDict)
    
    return 0


if __name__ == "__main__":
    exit(main())
    

# vim: set expandtab ts=4 sw=4:
