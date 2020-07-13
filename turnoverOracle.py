def turnoverOracle(ico):
    import numpy as np
    from aresApi import getCompanyData # napojuji Ares Api
    import joblib

    # nahravam prediktivni model
    model = joblib.load('turnoverModel.pkl')

    """Volam ARES api, abych zjistil data o firmě"""

    receivedCompanyData = getCompanyData(ico)
    for key, value in receivedCompanyData.items(): # Nahrazuje null v odpovědi za nulu
        if receivedCompanyData[key] == 'null':
          receivedCompanyData[key] = 0

    print(receivedCompanyData)

    """Ptam se na hodnotu nove poptavky"""

    # VAT (boolean), Legal entity(boolean), Hisotory in Months, Executives, Emmployees
    try:
        turnoverData = np.array([receivedCompanyData['Active Executives'],
                                  receivedCompanyData['Executives Records'],
                                  receivedCompanyData['History Months'],
                                  receivedCompanyData['Employees'],
                                  receivedCompanyData['Vat Payer'],
                                  receivedCompanyData['Limited Liability Company'],
                                  receivedCompanyData['Joint Stock Company'],
                                  receivedCompanyData['Bank Accounts']]
                                ).reshape(1,-1)
        turnoverValue = model.predict(turnoverData)
        turnoverValue = round(turnoverValue[0])*1000
    except:
        turnoverValue = 'cant predict'
    return turnoverValue

# test
'''
print(turnoverOracle('24259138'))
print(turnoverOracle('27074358'))
print(turnoverOracle('07822774'))
print(turnoverOracle('75854813'))
print(turnoverOracle('28901061'))
print(turnoverOracle('26185610'))
print(turnoverOracle('24299138'))
'''
