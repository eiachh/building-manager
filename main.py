from glob import glob
import json
import math
from common_lib.const import constants
from common_lib.utilities import utilities
from flask import Flask,request

class buildingManager():
    def __init__(self):
        self.request_data = ''

    def getCurrentStrategyToFollow(self):
        if(self.request_data['buildingLevels'][constants.ATTR_NAME_OF_METAL_MINE] < 15 ):
            return 1
        return 2

    def strategy1(self):
        pickedMine = 'None'
        print('Executing strategy 1')
        metalMineLevel = self.request_data['buildingLevels'][constants.ATTR_NAME_OF_METAL_MINE]
        crystalMineLevel = self.request_data['buildingLevels'][constants.ATTR_NAME_OF_CRYSTAL_MINE]
        
        hasEnergyFor = {'m': self.isEnergyEnough('m'), 'c': self.isEnergyEnough('c'), 'd': self.isEnergyEnough('d')}

        if(hasEnergyFor['m'] and hasEnergyFor['c']):
            if(metalMineLevel > (crystalMineLevel + 1)):
                pickedMine = 'c'
            else:
                pickedMine = 'm'
        elif(hasEnergyFor['m'] and (not hasEnergyFor['c'])):
            pickedMine = 'm'
        elif((not hasEnergyFor['m']) and hasEnergyFor['c']):
            pickedMine = 'c'

        if(hasEnergyFor['d']):
            pickedMine = self.strategy1CompareDeuMine(pickedMine)
        
        if(pickedMine != 'None'):
            pickedBuildingID = self.convertCharToOgameID(pickedMine)
            neededLevel = self.getCurrentLevelOfBuilding(pickedBuildingID) + 1
            return self.considerBuildingStorage(pickedBuildingID, neededLevel, 'NORMAL')
        else:
            prefferedEnergy = self.strategy1GetPrefferedEnergyBuilding()
            return self.considerBuildingStorage(prefferedEnergy['id'], prefferedEnergy['level'], 'NORMAL')

    def considerBuildingStorage(self, buildingID, buildingLevel, severity):
        attrName = constants.convertOgameIDToAttrName(buildingID)
        storageResp = ''
        if(self.isResourceEnough(attrName)):
            if(self.isNeededResourceCloseToStorageCap(attrName)):
                storageResp = self.pickWhichStorageToBuild(attrName)
            else:
                return self.buildResponseJson(buildingID, buildingLevel, severity)
        else:
            storageResp = self.pickWhichStorageToBuild(attrName)

        if(storageResp != 'None'):
            return self.buildResponseJson(storageResp['id'], storageResp['level'], 'NORMAL')
        else:
            return {'Result': 'None'}

    def strategy1GetPrefferedEnergyBuilding(self):
        ##TODO make this actually decide
        return {'id': constants.SOLAR_PLANT, 'level': self.request_data['buildingLevels'][constants.ATTR_NAME_OF_SOLAR_PLANT]}
      
    def buildResponseJson(self, buildingID, buildingLevel, severity):
        if(self.isResourceEnough(constants.convertOgameIDToAttrName(buildingID))):
            return {'buildingID': buildingID, 'buildingLevel': buildingLevel}
        else:
            return {'buildingID': -1, 'buildingLevel': -1}

    def convertCharToOgameID(self, char):
        if(char == 'm'):
            return constants.METAL_MINE
        if(char == 'c'):
            return constants.CRYSTAL_MINE
        if(char == 'd'):
            return constants.DEU_MINE

    def getCurrentLevelOfBuilding(self, ogameID):
        attrNameOfOgameID = constants.convertOgameIDToAttrName(ogameID)
        return self.request_data['buildingLevels'][attrNameOfOgameID]

    def strategy1CompareDeuMine(self, pickedMine):
        unifiedPrice = 0
        if(pickedMine == 'm'):
             unifiedPrice = utilities.getResourceSumInUnitPrice(self.request_data['buildingPrices'][constants.ATTR_NAME_OF_METAL_MINE])
        else:
            unifiedPrice = utilities.getResourceSumInUnitPrice(self.request_data['buildingPrices'][constants.ATTR_NAME_OF_CRYSTAL_MINE])

        unifiedPriceOfDeuMine = utilities.getResourceSumInUnitPrice(self.request_data['buildingPrices'][constants.ATTR_NAME_OF_DEU_MINE])

        if(unifiedPrice > (unifiedPriceOfDeuMine * 2)):
            return 'd'
        return pickedMine

    def strategyError(self):
        print('The strategy was not correctly picked')

    def isResourceEnough(self, attrName):
        if(self.request_data['allowanceResources']['Metal'] < self.request_data['buildingPrices'][attrName]['Metal']):
            return False
        if(self.request_data['allowanceResources']['Crystal'] < self.request_data['buildingPrices'][attrName]['Crystal']):
            return False
        if(self.request_data['allowanceResources']['Deuterium'] < self.request_data['buildingPrices'][attrName]['Deuterium']):
            return False
        return True
    
    def isNeededResourceCloseToStorageCap(self, attrName):
        percentageCap = 0.9
        if(self.request_data['allowanceResources']['Metal'] <= (self.request_data['buildingPrices'][attrName]['Metal'] * percentageCap)):
            return True
        if(self.request_data['allowanceResources']['Crystal'] <= (self.request_data['buildingPrices'][attrName]['Crystal'] * percentageCap)):
            return True
        if(self.request_data['allowanceResources']['Deuterium'] <= (self.request_data['buildingPrices'][attrName]['Deuterium'] * percentageCap)):
            return True
        return False

    def isEnergyEnough(self, pickedMine):
        currentEnergy =  self.request_data['actualResources']['Energy']
        neededEnergy = 0
        if(pickedMine == 'm'):
            neededEnergy = self.request_data['buildingPrices'][constants.ATTR_NAME_OF_METAL_MINE]['Energy']
        if(pickedMine == 'c'):
            neededEnergy = self.request_data['buildingPrices'][constants.ATTR_NAME_OF_CRYSTAL_MINE]['Energy']
        if(pickedMine == 'd'):
            neededEnergy = self.request_data['buildingPrices'][constants.ATTR_NAME_OF_DEU_MINE]['Energy']

        if(currentEnergy > neededEnergy):
            return True
        return False

    def pickWhichStorageToBuild(self, attrName):
        percentageCap = 0.8
        if(self.getStorageCapacity(self.request_data['buildingLevels'][constants.ATTR_NAME_OF_METAL_STORAGE]) <= (self.request_data['buildingPrices'][attrName]['Metal'] * percentageCap)):
            if(self.isResourceEnough(constants.ATTR_NAME_OF_METAL_STORAGE)):
                return {'id': constants.METAL_STORAGE, 'level': self.request_data['buildingLevels'][constants.ATTR_NAME_OF_METAL_STORAGE] + 1}

        if(self.getStorageCapacity(self.request_data['buildingLevels'][constants.ATTR_NAME_OF_CRYSTAL_STORAGE]) <= (self.request_data['buildingPrices'][attrName]['Crystal'] * percentageCap)):
            if(self.isResourceEnough(constants.ATTR_NAME_OF_CRYSTAL_STORAGE)):
                return {'id': constants.CRYSTAL_STORAGE, 'level': self.request_data['buildingLevels'][constants.ATTR_NAME_OF_CRYSTAL_STORAGE] + 1}

        if(self.getStorageCapacity(self.request_data['buildingLevels'][constants.ATTR_NAME_OF_DEU_STORAGE]) <= (self.request_data['buildingPrices'][attrName]['Deuterium'] * percentageCap)):
            if(self.isResourceEnough(constants.ATTR_NAME_OF_DEU_STORAGE)):
                return {'id': constants.DEU_STORAGE, 'level': self.request_data['buildingLevels'][constants.ATTR_NAME_OF_DEU_STORAGE] + 1}

        if(self.request_data['actualResources']['Deuterium'] == self.getStorageCapacity(self.request_data['buildingLevels'][constants.ATTR_NAME_OF_DEU_STORAGE])):
            return {'id': constants.DEU_STORAGE, 'level': self.request_data['buildingLevels'][constants.ATTR_NAME_OF_DEU_STORAGE] + 1}

        if(self.request_data['actualResources']['Crystal'] == self.getStorageCapacity(self.request_data['buildingLevels'][constants.ATTR_NAME_OF_CRYSTAL_STORAGE])):
            return {'id': constants.CRYSTAL_STORAGE, 'level': self.request_data['buildingLevels'][constants.ATTR_NAME_OF_CRYSTAL_STORAGE] + 1}

        if(self.request_data['actualResources']['Metal'] == self.getStorageCapacity(self.request_data['buildingLevels'][constants.ATTR_NAME_OF_METAL_STORAGE])):
            return {'id': constants.METAL_STORAGE, 'level': self.request_data['buildingLevels'][constants.ATTR_NAME_OF_METAL_STORAGE] + 1}
        
        return 'None'

    def getStorageCapacity(self, storageLevel):
        #God forgive me but I wont use the actual formula
        if(storageLevel == 0):
            return 10000
        if(storageLevel == 1):
            return 20000
        if(storageLevel == 2):
            return 40000
        if(storageLevel == 3):
            return 75000
        if(storageLevel == 4):
            return 140000
        if(storageLevel == 5):
            return 255000
        if(storageLevel == 6):
            return 470000
        if(storageLevel == 7):
            return 865000
        if(storageLevel == 8):
            return 1590000
        if(storageLevel == 9):
            return 2920000
        if(storageLevel == 10):
            return 5355000

    def getPreferredBuildingJson(self):
        strategy = self.getCurrentStrategyToFollow()
        if(strategy == 1):
            asdasd = self.strategy1()
            return self.strategy1()
        else:
            self.strategyError()

bldManager = buildingManager()

port = 5001
app = Flask(__name__)

@app.route('/get_prefered_building', methods=['GET'])
def getPreferedBuildingEndpoint():
    bldManager.request_data = request.get_json()
    respData = bldManager.getPreferredBuildingJson()
    return respData

@app.route('/ready', methods=['GET'])
def getReadiness():
    return "{Status: OK}"

app.run(host='0.0.0.0', port=port)