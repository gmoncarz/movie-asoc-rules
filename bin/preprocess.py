#!/usr/bin/env python
import argparse
import imdb
from pyzipcode import ZipCodeDatabase
import yaml
import re
import datetime
import shelve

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
CAST_SIZE = 5 
GENRE_SIZE = 3

class Movie:
    """ Class that represents a movie"""

    def __init__(self):
        """Default constructo """

        self.id = None
        self.name = None
        self.imdbName = None
        self.year = None
        self.yearCat = None
        self.director = None
        self.cast = None
        self.genre = None
        self.imdbRating = None
        self.rating = []


    def getExtraInfo(self, cache):
        """Load imdb information from file or IMDB server

        The function will try to read movie info from a text cache file. If 
        the movie ain't there, it will query IMDB server and store the output
        in the cache
        """
        if cache.has_key(self.id):
            self.name = cache[self.id].name
            self.imdbName = cache[self.id].imdbName
            self.year = cache[self.id].year
            self.director = cache[self.id].director
            self.cast = cache[self.id].cast
            self.genre = cache[self.id].genre
            self.imdbRating = cache[self.id].imdbRating
            self.rating = cache[self.id].rating
        else:
            self._queryImdb()
            cache[self.id] = self
        
        return
        

    def categorize(self):
        """Categorize some field related to movies"""
        if self.year:
            self.yearCat = unicode(self.year)[:-1] + u'0'


#    def _read(fh):
#        """Read movie information in the cache file.
#
#        Function returns:
#          * True: movie found
#          * False: movie not found
#        """
        

    def _queryImdb(self):
        """Get movie information from IMDB"""

        #return
        imdbObj = imdb.IMDb()
        try:
            imdbMovieObj = imdbObj.search_movie(self.imdbName)[0]
        except IndexError:
            print("Warning: movie %s was not found on IMDB." % self.imdbName)
            return

        if imdbMovieObj['long imdb canonical title'] == self.imdbName:
            imdbID = imdbMovieObj.getID()
            imdbMovieObj = imdbObj.get_movie(imdbID)

            if 'title' in imdbMovieObj.keys():
                self.name = imdbMovieObj['title']
            if 'year' in imdbMovieObj.keys():
                self.year = imdbMovieObj['year']
            if 'director' in imdbMovieObj.keys():
                self.director = imdbMovieObj['director'][0]['name']
            # Gets the main 5 actors
            if 'cast' in imdbMovieObj.keys():
                self.cast = list(map((lambda x: x['name']), imdbMovieObj['cast'][:CAST_SIZE]))
            else:
                self.Cast = None
            if 'rating' in imdbMovieObj.keys():
                self.imdbRating = imdbMovieObj['rating']
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
        age = int(age)

        self.id = uid
        self.sex = 'male' if sex[0].lower()=='m' else 'female'
        if   age<=17: self.ageCat = '0-17'
        elif age<=24: self.ageCat = '18-24'
        elif age<=34: self.ageCat = '25-34'
        elif age<=44: self.ageCat = '35-44'
        elif age<=49: self.ageCat = '45-49'
        elif age<=55: self.ageCat = '50-55'
        else:         self.ageCat = '56-inf'

        self.profession = professions[professionCode]
        self.postcode = postcode
    
    def getCiti(self):
        """ write the city and state given the postcode"""
        if self.postcode:
            zcdb = ZipCodeDatabase()
            regexp = re.compile(r'-\d*')
            try:
                postcode = re.sub(regexp, "", self.postcode)
                zipcode = zcdb[postcode]
                self.citi = zipcode.city
                self.state = zipcode.state
            except:
                self.citi = "NA-citi"
                self.state = "NA-state"
            

class Rating:
    """Rating representation"""

    def __init__(self):
        self.userid = None
        self.movieid = None
        self.rating = None
        self.ratingCat = None
        self.timestamp = None

    def categorize(self):
        if self.rating:
            rating = int(self.rating)
            if rating<=2: self.ratingCat = 'low'
            if rating==3: self.ratingCat = 'medium'
            if rating>=4: self.ratingCat = 'high'


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


def get_extra_info_from_movies(moviesDict, imdbFile):
    """Get additional info from the input movies files.

    The input is a dictionary of Movie object.
    """
    #fhWrite = open(imdbFile, "a")
    #fhRead = open(imdbFile, "r")
    cache = shelve.open(imdbFile)
    # XXX: limited to 10 rows just for testing
    #for movieObj in list(moviesDict.values())[:5]:
    for movieObj in list(moviesDict.values()):
        movieObj.getExtraInfo(cache)
        movieObj.categorize()

    cache.close()
    #fhWrite.close()
    #fhRead.close()

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
    


def getGenreList(moviesDict):
    genres = []
    for movie in moviesDict.values():
        if movie.genre:
            for genre in movie.genre:
                if not genre in genres:
                    genres.append(genre)

    return genres

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
        ratingObj.categorize()
        
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

    


def writeOutput1(filename, moviesDict, usersDict):

    # Open the File
    try:
        fh = open(filename, 'w')
    except:
        return None

    for movie in moviesDict.values():
        if movie.rating and movie.imdbRating:
            # Get the cast with the full size
            #cast = [None] * CAST_SIZE
            #cast = map((lambda x,y: x if x else ''), movie.cast, cast)
            #genre = [None] * GENRE_SIZE
            #genre = map((lambda x,y: x if x else ''), movie.genre, genre)
            cast = movie.cast[:CAST_SIZE] if movie.cast else [None]
            genres = movie.genre[:GENRE_SIZE] if movie.genre else [None]
            
            fixedMovie = [movie.id, movie.name, str(movie.year), movie.director, movie.imdbRating]
            for actor in cast:
                for genre in genres:
                    for rating in movie.rating:
                        user = usersDict[rating.userid]
                        fixedUser = [user.id, user.sex, user.ageCat, 
                          user.profession, user.citi, user.state]
                        fixedRating = [rating.rating, 
                          datetime.datetime.fromtimestamp(int(rating.timestamp)).year]

                        lst = fixedMovie[:]
                        lst.extend([actor, genre])
                        lst.extend(fixedUser)
                        lst.extend(fixedRating)
                        lst = map(unicode, lst)
                        line = '|'.join(lst)
                        fh.write(line.encode('utf-8'))
                        fh.write('\n')
    fh.close()



def writeOutputLikes1(filename, moviesDict, usersDict):

    CSV_CHAR = ','
    # Open the File
    try:
        fh = open(filename, 'w')
    except:
        return None

    # Write the header
    header = ['tid', 'name', 'year', 'director', 'actor', 'genre', 'uid', 'sex', 'ageCat', 'prefession', 'citi', 'state', 'rating']
    line = CSV_CHAR.join(header)
    fh.write(line.encode('utf-8'))
    fh.write('\n')
    

    transid = 0
    for movie in moviesDict.values():
        if movie.rating and movie.imdbRating:
            
            cast = movie.cast if movie.cast else ['?']
            genres = movie.genre if movie.genre else ['?']
            fixedMovie = ['"%s"' % movie.name, '"%s"' % movie.yearCat, 
              '"%s"' % movie.director ]
            for rating in movie.rating:
                transid += 1
                actor = '?'
                genre = '?'
                user = usersDict[rating.userid]
                fixedUser = ['"%s"' % user.id, '"%s"' % user.sex, 
                  '"%s"' % user.ageCat, '"%s"' % user.profession, 
                  '"%s"' % user.citi, '"%s"' % user.state]
                fixedRating = [ '"%s"' % rating.ratingCat]
 
                lst = [transid]
                lst.extend(fixedMovie[:])
                lst.extend([actor, genre])
                lst.extend(fixedUser)
                lst.extend(fixedRating)
                lst = map(unicode, lst)
                line = CSV_CHAR.join(lst)
                fh.write(line.encode('utf-8'))
                fh.write('\n')
               
                lstAct = ['?'] * len(lst)
                lstAct[0] = transid
                for actor in cast:
                    lstAct[4] = '"%s"' % actor

                    lstAct = map(unicode, lstAct)
                    line = CSV_CHAR.join(lstAct)
                    fh.write(line.encode('utf-8'))
                    fh.write('\n')
                    
                lstGen = ['?'] * len(lst)
                lstGen[0] = transid
                for genre in genres:
                    lstGen[5] = '"%s"' % genre

                    lstGen = map(unicode, lstGen)
                    line = CSV_CHAR.join(lstGen)
                    fh.write(line.encode('utf-8'))
                    fh.write('\n')
   
    fh.close()
    


def writeOutputLikes2(filename, moviesDict, usersDict):

    CSV_CHAR = ','
    # Open the File
    try:
        fh = open(filename, 'w')
    except:
        return None

    # Write the header
    header = ['tid', 'name', 'year', 'director', 'actor', 'genre', 'uid', 'sex', 'ageCat', 'prefession', 'citi', 'state', 'rating']
    line = CSV_CHAR.join(header)
    fh.write(line.encode('utf-8'))
    fh.write('\n')
    

    transid = 0
    for movie in moviesDict.values():
        if movie.rating and movie.imdbRating:
            
            cast = movie.cast if movie.cast else ['?']
            genres = movie.genre if movie.genre else ['?']
            fixedMovie = ['"%s"' % movie.name, '"%s"' % movie.yearCat, 
              '"%s"' % movie.director ]
            for rating in movie.rating:
                transid += 1
                actor = '?'
                genre = '?'
                user = usersDict[rating.userid]
                fixedUser = ['"%s"' % user.id, '"%s"' % user.sex, 
                  '"%s"' % user.ageCat, '"%s"' % user.profession, 
                  '"%s"' % user.citi, '"%s"' % user.state]
                fixedRating = [ '"%s"' % rating.ratingCat]
 
                lst = [transid]
                lst.extend(fixedMovie[:])
                lst.extend([actor, genre])
                lst.extend(fixedUser)
                lst.extend(fixedRating)
                lst = map(unicode, lst)
                line = CSV_CHAR.join(lst)
                fh.write(line.encode('utf-8'))
                fh.write('\n')
               
                lstAct = lst[:]
                for actor in cast:
                    lstAct[4] = '"%s"' % actor

                    lstAct = map(unicode, lstAct)
                    line = CSV_CHAR.join(lstAct)
                    fh.write(line.encode('utf-8'))
                    fh.write('\n')
                    
                lstGen = lst[:]
                for genre in genres:
                    lstGen[5] = '"%s"' % genre

                    lstGen = map(unicode, lstGen)
                    line = CSV_CHAR.join(lstGen)
                    fh.write(line.encode('utf-8'))
                    fh.write('\n')
   
    fh.close()
 


def writeOutputLikes3(filename, moviesDict, usersDict):

    CSV_CHAR = ','
    # Open the File
    try:
        fh = open(filename, 'w')
    except:
        return None

    # Write the header
    header = ['tid', 'name', 'year', 'director', 'actor', 'genre', 'uid', 'sex', 'ageCat', 'prefession', 'citi', 'state', 'rating']
    line = CSV_CHAR.join(header)
    fh.write(line.encode('utf-8'))
    fh.write('\n')
    

    transid = 0
    for movie in moviesDict.values():
        if movie.rating and movie.imdbRating:
            
            genres = movie.genre if movie.genre else ['?']
            fixedMovie = ['"%s"' % movie.name, '"%s"' % movie.yearCat, 
              '"%s"' % movie.director ]
            for rating in movie.rating:
                transid += 1
                actor = movie.cast[0] if movie.cast else ['?']
                user = usersDict[rating.userid]
                fixedUser = ['"%s"' % user.id, '"%s"' % user.sex, 
                  '"%s"' % user.ageCat, '"%s"' % user.profession, 
                  '"%s"' % user.citi, '"%s"' % user.state]
                fixedRating = [ '"%s"' % rating.ratingCat]
    
                for genre in genres:
 
                    lst = [transid]
                    lst.extend(fixedMovie[:])
                    lst.extend(['"%s"' % actor, '"%s"' % genre])
                    lst.extend(fixedUser)
                    lst.extend(fixedRating)
                    lst = map(unicode, lst)
                    line = CSV_CHAR.join(lst)
                    fh.write(line.encode('utf-8'))
                    fh.write('\n')
               
    fh.close()



def writeOutputLikes4(filename, moviesDict, usersDict, genreList):

    CSV_CHAR = ','
    # Open the File
    try:
        fh = open(filename, 'w')
    except:
        return None

    # Write the header
    header = ['name', 'year', 'director', 'actor', 'uid', 'sex', 'ageCat', 'prefession', 'citi', 'state', 'rating']
    genreHeader = list(map((lambda x: "genre_" + re.sub("'",'',x)), genreList[:]))
    header.extend(genreHeader)
    line = CSV_CHAR.join(header)
    fh.write(line.encode('utf-8'))
    fh.write('\n')
    

    for movie in moviesDict.values():
        if movie.rating and movie.imdbRating:
            
            genres = movie.genre if movie.genre else ['?']
            fixedMovie = ['"%s"' % movie.name, '"%s"' % movie.yearCat, 
              '"%s"' % movie.director ]
            for rating in movie.rating:
                actor = movie.cast[0] if movie.cast else ['?']
                user = usersDict[rating.userid]
                fixedUser = ['"%s"' % user.id, '"%s"' % user.sex, 
                  '"%s"' % user.ageCat, '"%s"' % user.profession, 
                  '"%s"' % user.citi, '"%s"' % user.state]
                fixedRating = [ '"%s"' % rating.ratingCat]

                genreDummy = map((lambda x: 'True' if x in movie.genre else '?'), genreList)
    
                lst = fixedMovie[:]
                lst.extend(['"%s"' % actor])
                lst.extend(fixedUser)
                lst.extend(fixedRating)
                lst.extend(genreDummy)
                lst = map(unicode, lst)
                line = CSV_CHAR.join(lst)
                fh.write(line.encode('utf-8'))
                fh.write('\n')
               
    fh.close()



def writeTransActorDirectors(filename, moviesDict, usersDict):
    """Write a transaction file ready to be process by R.

    It will write all the processed items on the target"""
    CSV_CHAR = ','
    # Open the File
    try:
        fh = open(filename, 'w')
    except:
        return None

    # Write the header
    header = ['tid', 'pid']
    line = CSV_CHAR.join(header)
    fh.write(line.encode('utf-8'))
    fh.write('\n')
    

    transid = 0
    for movie in moviesDict.values():
        if movie.rating and movie.imdbRating:
            
            cast = movie.cast if movie.cast else ['?']
            genres = movie.genre if movie.genre else ['?']
            fixedMovie = [movie.name, movie.yearCat, movie.director ]
            for rating in movie.rating:
                transid += 1
                user = usersDict[rating.userid]
                fixedUser = [user.id, user.sex, user.ageCat, user.profession, 
                  user.citi, user.state]
                fixedRating = [ rating.ratingCat]
 
                lst = fixedMovie[:]
                lst.extend(fixedUser)
                lst.extend(fixedRating)
                lst.extend(cast)
                lst.extend(genres)
                lst = map(unicode, lst)
                for item in lst:
                    fh.write(('%d,"%s"\n' %(transid, item)).encode('utf-8'))

    fh.close()



def writeOutputLikes5(filename, moviesDict, usersDict):
    """Write a transaction file ready to be process by R.

    It will write all the processed items on the target"""
    CSV_CHAR = ','
    # Open the File
    try:
        fh = open(filename, 'w')
    except:
        return None

    # Write the header
    header = ['tid', 'pid']
    line = CSV_CHAR.join(header)
    fh.write(line.encode('utf-8'))
    fh.write('\n')
    

    transid = 0
    for movie in moviesDict.values():
        if movie.rating and movie.imdbRating:
            
            cast = movie.cast if movie.cast else ['?']
            genres = movie.genre if movie.genre else ['?']
            fixedMovie = [movie.name, movie.yearCat, movie.director ]
            for rating in movie.rating:
                transid += 1
                user = usersDict[rating.userid]
                fixedUser = [user.id, user.sex, user.ageCat, user.profession, 
                  user.citi, user.state]
                fixedRating = [ rating.ratingCat]
 
                lst = fixedMovie[:]
                lst.extend(fixedUser)
                lst.extend(fixedRating)
                lst.extend(cast)
                lst.extend(genres)
                lst = map(unicode, lst)
                for item in lst:
                    fh.write(('%d,"%s"\n' %(transid, item)).encode('utf-8'))

    fh.close()


def writeTransActorsDirectors(filename, moviesDict, usersDict, ranking="high", 
  writeGenre=False, ratingYear=None):
    """Write a transaction file ready to be process by R.

    The file will write """
    CSV_CHAR = ','
    # Open the File
    try:
        fh = open(filename, 'w')
    except:
        return None

    # Write the header
    header = ['tid', 'pid']
    line = CSV_CHAR.join(header)
    fh.write(line.encode('utf-8'))
    fh.write('\n')
    
    transid = 0
    for movie in moviesDict.values():
        if movie.rating and movie.imdbRating:
            cast = map((lambda x: "actor_" + x), movie.cast) if movie.cast else ['?']
            genres = movie.genre if movie.genre else ['?']
            
            if movie.director:
                fixedMovie = [movie.name, "director_" + movie.director ]
            else:
                fixedMovie = [movie.name]
            
            for rating in movie.rating:
                if ranking == None or rating.ratingCat == ranking:
                    currentRatingYear = int(datetime.datetime.fromtimestamp(int(rating.timestamp)).strftime('%Y'))
                    if ratingYear==None or currentRatingYear in ratingYear:
                        transid += 1
                        user = usersDict[rating.userid]
                        fixedUser = [user.ageCat, "prof_" + user.profession]
                        fixedRating = [ rating.ratingCat ]
     
                        lst = fixedMovie[:]
                        lst.extend(fixedUser)
                        if ranking == None:
                            lst.extend(fixedRating)
                        lst.extend(cast)
                        if writeGenre:
                            lst.extend(map((lambda x: "genre_" + x), genres))
                        lst = map(unicode, lst)
                        for item in lst:
                            fh.write(('%d,"%s"\n' %(transid, item)).encode('utf-8'))

    fh.close()


def writeTransDirectors(filename, moviesDict, usersDict, ranking="high", writeGenre=False):
    """Write a transaction file ready to be process by R.

    The file will write """
    CSV_CHAR = ','
    # Open the File
    try:
        fh = open(filename, 'w')
    except:
        return None

    # Write the header
    header = ['tid', 'pid']
    line = CSV_CHAR.join(header)
    fh.write(line.encode('utf-8'))
    fh.write('\n')
    
    transid = 0
    for movie in moviesDict.values():
        if movie.rating and movie.imdbRating:
            genres = movie.genre if movie.genre else ['?']
            if movie.director:
                fixedMovie = [movie.name, "director_" + movie.director]
            else:
                fixedMovie = [movie.name]

            for rating in movie.rating:
                if ranking == None or rating.ratingCat == ranking:
                    transid += 1
                    user = usersDict[rating.userid]
                    fixedUser = [user.ageCat, "prof_" + user.profession]
                    fixedRating = [ rating.ratingCat ]
     
                    lst = fixedMovie[:]
                    lst.extend(fixedUser)
                    if ranking == None: 
                        lst.extend(fixedRating)
                    if writeGenre:
                        lst.extend(genres)
                    lst = map(unicode, lst)
                    for item in lst:
                        fh.write(('%d,"%s"\n' %(transid, item)).encode('utf-8'))

    fh.close()



def writeLocationMovie(filename, moviesDict, usersDict, ranking="high", citi=True, state=True, director=True):
    CSV_CHAR = ','
    # Open the File
    try:
        fh = open(filename, 'w')
    except:
        return None

    # Write the header
    header = ['tid', 'pid']
    line = CSV_CHAR.join(header)
    fh.write(line.encode('utf-8'))
    fh.write('\n')
    
    transid = 0
    for movie in moviesDict.values():
        if movie.rating and movie.imdbRating:
            genres = movie.genre if movie.genre else ['?']
            if movie.director and director:
                fixedMovie = [movie.name, "director_" + movie.director]
            else:
                fixedMovie = [movie.name]

            for rating in movie.rating:
                if ranking == None or rating.ratingCat == ranking:
                    transid += 1
                    user = usersDict[rating.userid]
                    fixedUser = []
                    if citi:    fixedUser.append(user.citi)
                    if state:   fixedUser.append(user.state)
                    fixedRating = [ rating.ratingCat ]
     
                    lst = fixedMovie[:]
                    lst.extend(fixedUser)
                    if ranking == None: 
                        lst.extend(fixedRating)
#                    if writeGenre:
#                        lst.extend(genres)
                    lst = map(unicode, lst)
                    for item in lst:
                        fh.write(('%d,"%s"\n' %(transid, item)).encode('utf-8'))

    fh.close()



def writeLocationGenre(filename, moviesDict, usersDict, ranking="high", citi=True, state=True, director=True):
    CSV_CHAR = ','
    # Open the File
    try:
        fh = open(filename, 'w')
    except:
        return None

    # Write the header
    header = ['tid', 'pid']
    line = CSV_CHAR.join(header)
    fh.write(line.encode('utf-8'))
    fh.write('\n')
    
    transid = 0
    for movie in moviesDict.values():
        if movie.rating and movie.imdbRating:
            genres = movie.genre if movie.genre else ['?']
            if movie.director and director:
                fixedMovie = [movie.name, "director_" + movie.director]
            else:
                fixedMovie = [movie.name]

            for rating in movie.rating:
                if ranking == None or rating.ratingCat == ranking:
                    transid += 1
                    user = usersDict[rating.userid]
                    fixedUser = []
                    if citi:    fixedUser.append(user.citi)
                    if state:   fixedUser.append(user.state)
                    fixedRating = [ rating.ratingCat ]
     
                    lst = fixedMovie[:]
                    lst.extend(fixedUser)
                    if ranking == None: 
                        lst.extend(fixedRating)
                    lst.extend(genres)
                    lst = map(unicode, lst)
                    for item in lst:
                        fh.write(('%d,"%s"\n' %(transid, item)).encode('utf-8'))

    fh.close()



def writeOnlyActorsDirectors(filename, moviesDict, usersDict, ranking=None, 
  actors=True, directors=True):
    """Write a transaction file ready to be process by R.

    The file will write """
    CSV_CHAR = ','
    # Open the File
    try:
        fh = open(filename, 'w')
    except:
        return None

    # Write the header
    header = ['tid', 'pid']
    line = CSV_CHAR.join(header)
    fh.write(line.encode('utf-8'))
    fh.write('\n')
    
    transid = 0
    for movie in moviesDict.values():
        if movie.rating and movie.imdbRating:
            cast = map((lambda x: "actor_" + x), movie.cast) if movie.cast else ['?']
            
            if directors and movie.director:
                fixedMovie = ["director_" + movie.director ]
            else:
                fixedMovie = []
            
            for rating in movie.rating:
                if ranking == None or rating.ratingCat in ranking:
                    transid += 1
                    user = usersDict[rating.userid]
                    fixedRating = [ rating.ratingCat ]
     
                    lst = fixedMovie[:]
                    lst.extend(fixedRating)
                    if actors:
                        lst.extend(cast)
                    lst = map(unicode, lst)
                    for item in lst:
                        fh.write(('%d,"%s"\n' %(transid, item)).encode('utf-8'))

    fh.close()



def alejo(filename, moviesDict, usersDict, ranking="high", 
  writeGenre=False, ratingYear=None):
    """Write a transaction file ready to be process by R.

    The file will write """
    CSV_CHAR = ','
    # Open the File
    try:
        fh = open(filename, 'w')
    except:
        return None

    # Write the header
    header = ['tid', 'pid']
    line = CSV_CHAR.join(header)
    fh.write(line.encode('utf-8'))
    fh.write('\n')
    
    transid = 0
    for movie in moviesDict.values():
        if movie.rating and movie.imdbRating:
            cast = map((lambda x: "actor_" + x), movie.cast) if movie.cast else ['?']
            genres = movie.genre if movie.genre else ['?']
            
            if movie.director:
                fixedMovie = [movie.name, "director_" + movie.director ]
            else:
                fixedMovie = [movie.name]
            
            for rating in movie.rating:
                if ranking == None or rating.ratingCat == ranking:
                    currentRatingYear = int(datetime.datetime.fromtimestamp(int(rating.timestamp)).strftime('%Y'))
                    if ratingYear==None or currentRatingYear in ratingYear:
                        transid += 1
                        user = usersDict[rating.userid]
                        fixedUser = [user.ageCat, "prof_" + user.profession, user.citi, user.state, user.sex]
                        fixedRating = [ rating.ratingCat ]
     
                        lst = fixedMovie[:]
                        lst.extend(fixedUser)
                        if ranking == None:
                            lst.extend(fixedRating)
                        lst.extend(cast)
                        if writeGenre:
                            lst.extend(map((lambda x: "genre_" + x), genres))
                        lst = map(unicode, lst)
                        for item in lst:
                            fh.write(('%d,"%s"\n' %(transid, item)).encode('utf-8'))

    fh.close()






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
    imdbFile = "%s/%s" %  \
      (config['output']['base_path'], config['output']['imdb'])
    output1File = "%s/%s" %  \
      (config['output']['base_path'], config['output']['file1'])
    outputFileLike1 = "%s/%s" %  \
      (config['output']['base_path'], config['output']['fileLike1'])
    outputFileLike2 = "%s/%s" %  \
      (config['output']['base_path'], config['output']['fileLike2'])
    outputFileLike3 = "%s/%s" %  \
      (config['output']['base_path'], config['output']['fileLike3'])
    outputFileLike4 = "%s/%s" %  \
      (config['output']['base_path'], config['output']['fileLike4'])
    outputFileLike5 = "%s/%s" %  \
      (config['output']['base_path'], config['output']['fileLike5'])
    outputFileLike6 = "%s/%s" %  \
      (config['output']['base_path'], config['output']['fileLike6'])
    outputFileLike7 = "%s/%s" %  \
      (config['output']['base_path'], config['output']['fileLike7'])
    outputFileLike8 = "%s/%s" %  \
      (config['output']['base_path'], config['output']['fileLike8'])
    outputFileLike9 = "%s/%s" %  \
      (config['output']['base_path'], config['output']['fileLike9'])
    outputFileLike10 = "%s/%s" %  \
      (config['output']['base_path'], config['output']['fileLike10'])
    outputFileLike11 = "%s/%s" %  \
      (config['output']['base_path'], config['output']['fileLike11'])
    outputFileLike12 = "%s/%s" %  \
      (config['output']['base_path'], config['output']['fileLike12'])
    outputFileLike13 = "%s/%s" %  \
      (config['output']['base_path'], config['output']['fileLike13'])
    outputLocationCitiMovie = "%s/%s" %  \
      (config['output']['base_path'], config['output']['fileLocationCitiMovie'])
    outputLocationStateMovie = "%s/%s" %  \
      (config['output']['base_path'], config['output']['fileLocationStateMovie'])
    outputLocationCitiGenre = "%s/%s" %  \
      (config['output']['base_path'], config['output']['fileLocationCitiGenre'])
    outputLocationStateGenre = "%s/%s" %  \
      (config['output']['base_path'], config['output']['fileLocationStateGenre'])
    outputFileLike2000 = "%s/%s" %  \
      (config['output']['base_path'], config['output']['fileLike2000'])
    outputFileLike2001 = "%s/%s" %  \
      (config['output']['base_path'], config['output']['fileLike2001'])
    outputFileLike2002 = "%s/%s" %  \
      (config['output']['base_path'], config['output']['fileLike2002'])
    outputActors = "%s/%s" %  \
      (config['output']['base_path'], config['output']['fileActors'])
    outputDirectors = "%s/%s" %  \
      (config['output']['base_path'], config['output']['fileDirectors'])

    # Load all movies
    moviesDict = load_movies(movieFile)
    # get extra info from IMDB    
    get_extra_info_from_movies(moviesDict, imdbFile)

#    # Get the genre list
#    genreList = getGenreList(moviesDict)

    # Load all the users
    usersDict = load_users(userFile)
    # Get the citi and state
    for user in usersDict.values():
        user.getCiti()

    # Load rating
    ratingSet = load_rating(ratingFile)
    assign_rating(ratingSet, moviesDict, usersDict)

##    writeOutputLikes1(outputFileLike1, moviesDict, usersDict)
##    writeOutputLikes2(outputFileLike2, moviesDict, usersDict)
##    writeOutputLikes3(outputFileLike3, moviesDict, usersDict)
##    writeOutputLikes4(outputFileLike4, moviesDict, usersDict, genreList)
##    writeOutputLikes5(outputFileLike5, moviesDict, usersDict)
##    writeTransActorsDirectors(outputFileLike6, moviesDict, usersDict, ranking="high")
##    writeTransDirectors(outputFileLike7, moviesDict, usersDict, ranking="high")
##    writeTransActorsDirectors(outputFileLike8, moviesDict, usersDict, ranking="low")
##    writeTransDirectors(outputFileLike9, moviesDict, usersDict, ranking="low")
#    writeTransActorsDirectors(outputFileLike10, moviesDict, usersDict, 
#      ranking=None, writeGenre=True)
#    writeTransActorsDirectors(outputFileLike11, moviesDict, usersDict, 
#      ranking=None, writeGenre=False)
#    writeTransDirectors(outputFileLike12, moviesDict, usersDict, 
#      ranking=None, writeGenre=True)
#    writeTransDirectors(outputFileLike13, moviesDict, usersDict, 
#      ranking=None, writeGenre=False)
#    writeLocationMovie(outputLocationCitiMovie, moviesDict, usersDict, 
#      ranking=None, citi=True, state=False, director=False )
#    writeLocationMovie(outputLocationStateMovie, moviesDict, usersDict, 
#      ranking=None, citi=False, state=True, director=True )
#    writeLocationGenre(outputLocationCitiGenre, moviesDict, usersDict, 
#      ranking=None, citi=True, state=False, director=False )
#    writeLocationGenre(outputLocationStateGenre, moviesDict, usersDict, 
#      ranking=None, citi=False, state=True, director=False )
#    writeTransActorsDirectors(outputFileLike2000, moviesDict, usersDict, 
#      ranking=None, writeGenre=False, ratingYear=(2000,))
#    writeTransActorsDirectors(outputFileLike2001, moviesDict, usersDict, 
#      ranking=None, writeGenre=False, ratingYear=(2001,))
#    writeTransActorsDirectors(outputFileLike2002, moviesDict, usersDict, 
#      ranking=None, writeGenre=False, ratingYear=range(2002,2015))
#    writeOnlyActorsDirectors(outputDirectors, moviesDict, usersDict, 
#      ranking=["high", "low"], actors=False, directors=True )
#    writeOnlyActorsDirectors(outputActors, moviesDict, usersDict, 
#      ranking=["high", "low"], actors=True, directors=False )
#    writeTransActorsDirectors(outputFileLike2002, moviesDict, usersDict, 
#      ranking=None, writeGenre=False, ratingYear=range(2002,2015))
    alejo(outputFileLike2000, moviesDict, usersDict,
        ranking=None, writeGenre=True, ratingYear=(2000,))
    alejo(outputFileLike2001, moviesDict, usersDict,
        ranking=None, writeGenre=True, ratingYear=(2001,))
    alejo(outputFileLike2002, moviesDict, usersDict,
        ranking=None, writeGenre=True, ratingYear=range(2002,2015))

    return 0


if __name__ == "__main__":
    exit(main())
    

# vim: set expandtab ts=4 sw=4:
