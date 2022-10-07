from glob import glob
import json
import math
from const import constants
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
            return self.buildResponseJson(pickedBuildingID, neededLevel, 'NORMAL')
        else:
            prefferedEnergy = self.strategy1GetPrefferedEnergyBuilding()
            return self.buildResponseJson(prefferedEnergy['id'], prefferedEnergy['level'], 'NORMAL')

    def strategy1GetPrefferedEnergyBuilding(self):
        ##TODO make this actually decide
        return {'id': constants.SOLAR_PLANT, 'level': self.request_data['buildingLevels'][constants.ATTR_NAME_OF_SOLAR_PLANT]}
      
    def buildResponseJson(self, buildingID, buildingLevel, severity):
        return {'buildingID': buildingID, 'buildingLevel': buildingLevel, 'severity': severity}

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
             unifiedPrice = constants.getResourceSumInUnitPrice(self.request_data['buildingPrices'][constants.ATTR_NAME_OF_METAL_MINE])
        else:
            unifiedPrice = constants.getResourceSumInUnitPrice(self.request_data['buildingPrices'][constants.ATTR_NAME_OF_CRYSTAL_MINE])

        unifiedPriceOfDeuMine = constants.getResourceSumInUnitPrice(self.request_data['buildingPrices'][constants.ATTR_NAME_OF_DEU_MINE])

        if(unifiedPrice > (unifiedPriceOfDeuMine * 3)):
            return 'd'
        return pickedMine

    def strategyError(self):
        print('The strategy was not correctly picked')

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

    def getPrefferedBuildingJson(self):
        strategy = self.getCurrentStrategyToFollow()
        if(strategy == 1):
            return self.strategy1()
        else:
            self.strategyError()

bldManager = buildingManager()

port = 5001
app = Flask(__name__)

@app.route('/get_prefered_building', methods=['GET'])
def getPreferedBuildingEndpoint():
    bldManager.request_data = request.get_json()
    return bldManager.getPrefferedBuildingJson()

@app.route('/ready', methods=['GET'])
def getReadiness():
    return "{Status: OK}"

app.run(host='0.0.0.0', port=port)