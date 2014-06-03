#!/usr/bin/env python
import argparse
import imdb
from pyzipcode import ZipCodeDatabase
import yaml
import re

professions = {
    '0': 'unknown',
    '1': 'other',
    '2': 'academic / teacher',
    '3': 'Artist',
    '4': 'administrative',
    '5': 'university/postgrade student',
    '6': 'customer service',
    '7': 'doctor / health care',
    '8': 'executive',
    '9': 'farmer',
    '10': 'housewife',
    '11': 'primary student',
    '12': 'layers',
    '13': 'coder',
    '14': 'retired',
    '15': 'sales / marketing',
    '16': 'scientist',
    '17': 'independent',
    '18': 'tecnic / engineer',
    '19': 'business / craftsman',
    '20': 'unemployer',
    '21': 'writer',
    }

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
        self.rating = []


    def getExtraInfo(self):
        """Get additiong information from IMDB"""

        return
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

            


class User:
    """User representation class"""

    def __init__(self):
        self.id = None
        self.sex = None     # male or female
        """ageCat possible values:
          * 0-17
          * 18-24
          * 25-34
          * 35-44
          * 45-49
          * 50-55
          * 56-inf
        """
        self.ageCat = None  
        self.profession = None
        self.postcode = None
        self.citi = None
        self.state = None
        self.rating = []

    def fromFile(self, lst):
        """load an user from the user.txt line"""
        (uid, sex, age, professionCode, postcode) = lst

        self.id = uid
        self.sex = 'male' if sex[0].lower()=='m' else 'female'
        if   age<=17: self.ageCat = '0-17'
        elif age<=24: self.ageCat = '18-24'
        elif age<=34: self.ageCat = '25-34'
        elif age<=44: self.ageCat = '35-44'
        elif age<=49: self.ageCat = '45-49'
        elif age<=55: self.ageCat = '50-55'
        else:         self.ageCat = '56-inf'

        self.proffesion = professions[professionCode]
        self.postcode = postcode
    
    def getCiti(self):
        """ write the city and state given the postcode"""
        if self.postcode:
            zcdb = ZipCodeDatabase()
            zipcode = zcdb[48067]
            self.citi = zipcode.city
            self.state = zipcode.state
            

class Rating:
    """Rating representation"""

    def __init__(self):
        self.userid = None
        self.movieid = None
        self.rating = None
        self.timestamp = None



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
        if movieID not in ret:
            # The movie is not in the dictionary. Lets add it
            # 1st Construct the Movie Obj
            movie = Movie()
            movie.id = movieID
            movie.imdbName = name
            movie.genre = genres.split('|')
            
            # 2nd Add it to the return dict
            ret[movie.id] = movie

    return ret
    


def load_users(filename):
    """Return a dictionary of User objects given a movies input file"""

    usersGen = read_csv_from_file(filename,  sep='::')
    if not usersGen:
        print("Error reading users file")
        return None
    
    ret = {}
    # Iterate over all the file
    for line in usersGen:
        userID = line[0]
        if userID not in ret:
            user = User()
            user.fromFile(line)
            ret[userID] = user

    return ret
 


def load_rating(filename):
    """Return a dictionary of movies objects given a movies input file"""

    ratingGen = read_csv_from_file(filename,  sep='::')
    if not ratingGen:
        print("Error reading rating file")
        return None
    
    ret = set()
    # Iterate over all the file
    for line in ratingGen:
        (userid, movieid, rating, timestamp) = line
        ratingObj = Rating()
        ratingObj.userid = userid
        ratingObj.movieid = movieid
        ratingObj.rating = rating
        ratingObj.timestamp = timestamp
        
        ret.add(ratingObj)

    return ret



def assign_rating(ratingSet, moviesDict=None, usersDict=None):
    """Assign rating to users or movies

    Given a set of Rating object, it is assigned to a movie or user
    dictionary
    """
    for ratingObj in ratingSet:
        # Add the rating into the movies dict
        if moviesDict and ratingObj.movieid in moviesDict:
            moviesDict[ratingObj.movieid].rating.append(ratingObj)
        # Add the rating into the users dict
        if usersDict and ratingObj.userid in usersDict:
            usersDict[ratingObj.userid].rating.append(ratingObj)

    return



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
    movieFile = "%s/%s" %  \
      (config['input']['base_path'], config['input']['movie'])
    userFile = "%s/%s" %  \
      (config['input']['base_path'], config['input']['user'])
    ratingFile = "%s/%s" %  \
      (config['input']['base_path'], config['input']['rating'])

    # Load all movies
    moviesDict = load_movies(movieFile)
    # get extra info from IMDB    
    get_extra_info_from_movies(moviesDict)

    # Load all the users
    usersDict = load_users(userFile)
    # Get the citi and state
    for user in usersDict.values():
        user.getCiti()

    # Load rating
    ratingSet = load_rating(ratingFile)
    
    assign_rating(ratingSet, moviesDict, usersDict)
    import pdb; pdb.set_trace()
    return 0


if __name__ == "__main__":
    exit(main())
    

# vim: set expandtab ts=4 sw=4:
