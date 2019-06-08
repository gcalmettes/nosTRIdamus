const { getFilteredRaces } = require('./utils.js');

// page to scrape from
const url = 'http://www.ironman.com/events/triathlon-races.aspx'

// path to save
const savePath = "./../data/races/"

// Active IronMan races
let outputFileName = 'ironMan-active-races'
let filterWords = ['IRONMAN 70.3', 'IRONMAN']

getFilteredRaces({ url, filterWords, outputFileName,  path: savePath})


// IronKids
outputFileName = 'ironKids-races'
filterWords = ['IronKids']

getFilteredRaces({ url, filterWords, outputFileName,  path: savePath})

