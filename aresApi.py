def getCompanyData(ico):
    import requests
    import xml.etree.ElementTree as ET
    import datetime
    payload = {'ico': ico}
    companyData = {}

    # Napojuji databázi STD
    std = requests.get('http://wwwinfo.mfcr.cz/cgi-bin/ares/darv_std.cgi', params=payload)
    std.encoding = 'utf-8'
    stdTree = ET.fromstring(std.text)
    stdPrefix = {'are': 'http://wwwinfo.mfcr.cz/ares/xml_doc/schemas/ares/ares_answer/v_1.0.1',
                 'dtt': 'http://wwwinfo.mfcr.cz/ares/xml_doc/schemas/ares/ares_datatypes/v_1.0.4'}

    # Napojuji databázi RES
    res = requests.get('https://wwwinfo.mfcr.cz/cgi-bin/ares/darv_res.cgi', params=payload)
    res.encoding = 'utf-8'
    resTree = ET.fromstring(res.text)
    resPrefix = {'are': 'http://wwwinfo.mfcr.cz/ares/xml_doc/schemas/ares/ares_answer_res/v_1.0.3',
                 'D': 'http://wwwinfo.mfcr.cz/ares/xml_doc/schemas/ares/ares_datatypes/v_1.0.3'}

    # Napojuji databázi VREO
    vreo = requests.get('https://wwwinfo.mfcr.cz/cgi-bin/ares/darv_vreo.cgi', params=payload)
    vreo.encoding = 'utf-8'
    vreoTree = ET.fromstring(vreo.text)
    vreoPrefix = {'are': 'http://wwwinfo.mfcr.cz/ares/xml_doc/schemas/ares/ares_answer_vreo/v_1.0.0'}

    # Napojuji databázi DPH
    dphData = """ <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:roz="http://adis.mfcr.cz/rozhraniCRPDPH/">
    <soapenv:Body>
      <roz:StatusNespolehlivyPlatceRozsirenyRequest>
        <roz:dic>""" + payload['ico'] + """</roz:dic>
      </roz:StatusNespolehlivyPlatceRozsirenyRequest>
    </soapenv:Body>
  </soapenv:Envelope>
  """
    headers = {'Content-Type': 'text/xml', 'Connection': 'keep-alive'}
    dph = requests.post('http://adisrws.mfcr.cz/adistc/axis2/services/rozhraniCRPDPH.rozhraniCRPDPHSOAP', data=dphData,
                        headers=headers)
    dph.encoding = 'utf-8'
    dphTree = ET.fromstring(dph.text)
    dphPrefix = {'soapenv': 'http://schemas.xmlsoap.org/soap/envelope/', 'roz': 'http://adis.mfcr.cz/rozhraniCRPDPH/'}

    # Ověřuji zda subjekt existuje
    icoCheckList = stdTree.findall('are:Odpoved/are:Pocet_zaznamu', stdPrefix)
    icoCheck = int(icoCheckList[0].text)
    companyData['Company Exists'] = icoCheck

    # Pokud pod daným IČO existuje firma, pak zjišťuji data o dané firmě
    if icoCheck != 0:

        # Zjišťuji název společnosti
        checkNameList = stdTree.findall('are:Odpoved/are:Zaznam/are:Obchodni_firma', stdPrefix)
        if len(checkNameList) != 0:  # check jestli našlo
            name = checkNameList[0].text
            companyData['Name'] = name
        else:
            companyData['Name'] = 'null'

        # Zjišťuji registraci k DPH

        dphList = dphTree.findall('soapenv:Body/roz:StatusNespolehlivyPlatceRozsirenyResponse/roz:statusPlatceDPH',
                                  dphPrefix)
        if dphList[0].attrib['nespolehlivyPlatce'] != 'NENALEZEN':  # check jestli našlo
            companyData['Vat Payer'] = 1
            companyData['Tax Office No'] = dphList[0].attrib['cisloFu']
        else:
            companyData['Vat Payer'] = 0
            companyData['Tax Office No'] = 'null'

        # Zjišťuji počet evidovaných bankovních účtů

        dphList = dphTree.findall(
            'soapenv:Body/roz:StatusNespolehlivyPlatceRozsirenyResponse/roz:statusPlatceDPH/roz:zverejneneUcty',
            dphPrefix)
        if len(dphList) != 0:  # check jestli našlo
            accounts = 0
            for accountBox in dphList[0]:
                for account in accountBox:
                    accounts += 1
            companyData['Bank Accounts'] = accounts
        else:
            companyData['Bank Accounts'] = 'null'

        # Zjišťuji právní formu

        limitedLiabilityCode = '112'
        jointStockCode = '121'

        checkLegalEntityList = stdTree.findall('are:Odpoved/are:Zaznam/are:Pravni_forma/dtt:Kod_PF', stdPrefix)
        if len(checkLegalEntityList) != 0:  # check jestli našlo
            legalEntity = checkLegalEntityList[0].text
            companyData['Legal Entity'] = legalEntity
            companyData['Limited Liability Company'] = 0
            companyData['Joint Stock Company'] = 0
            if legalEntity == limitedLiabilityCode:
                companyData['Limited Liability Company'] = 1
            if legalEntity == jointStockCode:
                companyData['Joint Stock Company'] = 1
        else:
            companyData['Legal Entity'] = 'null'

        # Zjišťuji počet jednatelů a záznamů o jednatelích
        executivesList = vreoTree.findall('are:Odpoved/are:Vypis_VREO/are:Statutarni_organ/are:Clen', vreoPrefix)
        if len(executivesList) != 0:  # check jestli našlo
            executivesRecords = 0
            activeExecutives = 0
            for i in range(
                    len(executivesList)):  # prochází záznamy a počítá počet aktivních exectuvies (bez záznamu 'dvy)
                member = executivesList[i].attrib
                executivesRecords += 1
                if not 'dvy' in member:
                    activeExecutives += 1
            companyData['Active Executives'] = activeExecutives
            companyData['Executives Records'] = executivesRecords
        else:
            companyData['Active Executives'] = 'null'
            companyData['Executives Records'] = 'null'

        # Zjišťuji dobu od založení (v měsících)
        foundationDateList = stdTree.findall('are:Odpoved/are:Zaznam/are:Datum_vzniku', stdPrefix)
        if len(foundationDateList) != 0:  # check jestli našlo
            foundationDate = foundationDateList[0].text
            foundationDate = datetime.datetime.strptime(foundationDate, '%Y-%m-%d')
            today = datetime.date.today()
            historyMonths = (
                                        today.year - foundationDate.year) * 12  # počítá počet měsíců mezi založením a aktuálním datem
            companyData['History Months'] = historyMonths
        else:
            companyData['History Months'] = 'null'

        # Zjišťuji počet zaměstnanců
        employeesList = resTree.findall('are:Odpoved/D:Vypis_RES/D:SU/D:KPP', resPrefix)
        if len(employeesList) != 0 and employeesList[
            0].text == 'Bez zaměstnanců':  # check jestli našlo a zda není vyplněno 'Bez zaměstnanců'
            companyData['Employees'] = 0
        elif len(employeesList) != 0 and employeesList[
            0].text != 'Neuvedeno':  # check jestli našlo a zda není vyplněno 'Neuvedeno'
            employeesString = employeesList[0].text
            employeesString = employeesString.split(" ")
            employees = round((int(employeesString[0]) + int(
                employeesString[2])) / 2)  # počítá střed intervalu uvádějícího počet zaměstnanců
            companyData['Employees'] = employees
        else:
            companyData['Employees'] = 'null'

    # Vracím výsledky
    return companyData

#test
'''
print(getCompanyData('27074358'))
print(getCompanyData('07822774'))
print(getCompanyData('24259138'))
print(getCompanyData('75854813'))
print(getCompanyData('28901061'))
print(getCompanyData('26185610'))
print(getCompanyData('24299138'))
'''