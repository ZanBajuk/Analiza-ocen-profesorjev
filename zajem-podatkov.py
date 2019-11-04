import requests as req
import os
import re
import csv

url_strani = "http://www.profesorji.net"
mapa_fakultet = "fakultete"
datoteka_fakultet = "index_fakultete.html"

mapa_podatkov_profesorjev = "profesorji"
datoteka_podatkov_profesorjev = "ocene_profesorjev.csv"

def prevedi_stran_v_niz(url):
    try:
        # del kode, ki morda sproži napako
        stran = req.get(url)
    except req.exceptions.ConnectionError:
        # koda, ki se izvede pri napaki
        # dovolj je če izpišemo opozorilo in prekinemo izvajanje funkcije
        print("Napaka pri povezovanju do:", url)
        return None
    # nadaljujemo s kodo če ni prišlo do napake
    if stran.status_code == req.codes.ok:
        return stran.text
    else:
        print("Napaka pri prenosu strani:", url)
        return None

def shrani_niz_v_datoteko(text, directory, filename):
    """Funkcija zapiše vrednost parametra "text" v novo ustvarjeno datoteko
    locirano v "directory"/"filename", ali povozi obstoječo. V primeru, da je
    niz "directory" prazen datoteko ustvari v trenutni mapi.
    """
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, filename)
    with open(path, 'w', encoding='utf-8') as file_out:
        file_out.write(text)
    return None

def shrani_stran_v_datoteko(url, directory, filename):
    """Funkcija vrne celotno vsebino datoteke "directory"/"filename" kot niz"""
    text = prevedi_stran_v_niz(url)
    shrani_niz_v_datoteko(text, directory, filename)
    print("Stran: {}, shranjena v {}, kot {}".format(url, directory, filename))

def prevedi_datoteko_v_niz(directory, filename):
    """Funkcija vrne celotno vsebino datoteke "directory"/"filename" kot niz"""
    path = os.path.join(directory, filename)
    with open(path, 'r', encoding="utf8") as file_in:
        return file_in.read()

def iz_strani_v_univerze(stran):
    #Dobimo bloke univerz
    rx = re.compile(r"(Univerza.*?</tbody>)",re.UNICODE | re.DOTALL)
    #r"(?P<ime_univerze>Univerza.*?)</h1>(?P<blok>.*?)</tbody>"
    f = re.findall(rx, stran)
    rx2 = re.compile(r"(?P<ime_univerze>Univerza.*?)</h1>(?P<fakultete>.*?)</tbody>",re.UNICODE | re.DOTALL)
    return [re.search(rx2, i).groupdict() for i in f]

def iz_univerze_v_fakultete(blok):
    #Dobimo fakultete posameznih univerz
    rx = re.compile(r'href=".*?</a>', re.DOTALL)
    f = re.findall(rx, blok)
    rx2 = re.compile(r'href="(?P<url>.*?)">(?P<ime>.*?)</a>', re.DOTALL)
    return [re.search(rx2, i).groupdict() for i in f if re.search(rx2, i).groupdict()["url"] != r"/fakulteta/pf"]

def iz_fakultete_v_smeri_fakultet(blok):
    rx = re.compile(r'.*?href="(.*?)">', re.DOTALL)
    return re.findall(rx, blok)

def iz_smeri_fakultet_v_url(stran):
    rx = re.compile(r'href="(.*?)">.*?</a.*?\(\d+\)', re.DOTALL)
    return re.findall(rx, stran)

def iz_strani_profesorjov_v_profesorje(stran):
    rx = re.compile(r'<li>(<a href=".*?">.*?</a>)</li>', re.DOTALL)
    f = re.findall(rx, stran)
    rx2 = re.compile(r'<a href="(?P<url>.*?)">(?P<ime_profesorja>.*?)</a>', re.DOTALL)
    return [re.search(rx2, i).groupdict() for i in f]

def poberi_podatke_profesorjev(stran):
    rx = re.compile(r'<meta name="Description" content="Profesor .*?,.*?Ocena:(?P<ocena>.*?)/5 \((?P<st_ocen>\d*?) ocen\)\. Predmeti: (?P<predmeti>.*?)\.">', re.DOTALL)
    return re.search(rx, stran).groupdict()

def zdruzi_podatke_profesorja(d1, d2):
    d1["predmeti"]+=d2["predmeti"]
    skupno_st_ocen = d1["st_ocen"] + d2["st_ocen"]
    if skupno_st_ocen > 0:
        d1["ocena"] = d1["ocena"] * (d1["st_ocen"] / skupno_st_ocen) + d2["ocena"] * (d2["st_ocen"] / skupno_st_ocen)
    d1["st_ocen"] = skupno_st_ocen
    return d1

def preveri_ce_profesor_v_2_smereh(novi_profesor, sez):
    for profesor in sez:
                    if novi_profesor["ime"] == profesor["ime"]:
                        a = zdruzi_podatke_profesorja(profesor, novi_profesor)
                        sez.remove(profesor)
                        sez.append(a)
                        return sez
    return sez.append(novi_profesor)

def zgradi_csv(fieldnames, rows, directory, filename):
    """
    Funkcija v csv datoteko podano s parametroma "directory"/"filename" zapiše
    vrednosti v parametru "rows" pripadajoče ključem podanim v "fieldnames"
    """
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, filename)
    with open(path, 'w', encoding='utf-8') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return None

#shrani_stran_v_datoteko(url_strani, mapa_fakultet, datoteka_fakultet)
print("Done")

def main(redownload=True):
    #Seznam v katerega bomo vnesli vse podatke profesorjev
    tabela_profesorjev = []

    #shrani_stran_v_datoteko(url_strani, mapa_fakultet, datoteka_fakultet)
    stran = prevedi_datoteko_v_niz(mapa_fakultet, datoteka_fakultet)

    #Seznam slovarjev, ki vsebuje ime univerze in blok, ki vsebuje fakultete
    univerze = iz_strani_v_univerze(stran)

    #Prevedemo v seznam slovarjev, ki vsebuje ime univerze in podslovar, ki vsebuje ime fakultet in url naslove, ki vodijo do ocen
    for i in univerze:
        i["fakultete"] = iz_univerze_v_fakultete(i["fakultete"])

    #Shranimo smeri fakultet v svoje datoteke
    for univerza in univerze:
        for fakulteta in univerza["fakultete"]:
            url = url_strani + fakulteta["url"]
            mapa = os.path.join(mapa_fakultet, univerza["ime_univerze"], fakulteta["ime"])
            ime = f'index_{fakulteta["ime"]}.html'
            if redownload:
                shrani_stran_v_datoteko(url, mapa, ime)
            else:
                if not os.path.isfile(os.path.join(mapa, ime)):
                    shrani_stran_v_datoteko(url, mapa, ime)

    #Vsaki fakulteti url spremenimo v seznam url-jev smeri. Smeri med seboj nebomo ločili saj je pri večina smermi 0 ali 1 profesor/ica
    for univerza in univerze:
        for fakulteta in univerza["fakultete"]:
            mapa = os.path.join(mapa_fakultet, univerza["ime_univerze"], fakulteta["ime"])
            ime = f'index_{fakulteta["ime"]}.html'
            stran = prevedi_datoteko_v_niz(mapa, ime)
            fakulteta["url"] = iz_smeri_fakultet_v_url(stran)

    #Shranimo stran profesorjev na vsaki smeri vsake fakultete
    for univerza in univerze:
        for fakulteta in univerza["fakultete"]:
            for i in range(len(fakulteta["url"])):
                mapa = os.path.join(mapa_fakultet, univerza["ime_univerze"], fakulteta["ime"])
                url = url_strani + fakulteta["url"][i]
                ime = f'index_smer{i}.html'
                if redownload:
                    shrani_stran_v_datoteko(url, mapa, ime)
                else:
                    if not os.path.isfile(os.path.join(mapa, ime)):
                        shrani_stran_v_datoteko(url, mapa, ime)

    #V seznam shranimo profesorje in url-je do njihovih strani
    for univerza in univerze:
        for fakulteta in univerza["fakultete"]:
            for i in range(len(fakulteta["url"])):
                mapa = os.path.join(mapa_fakultet, univerza["ime_univerze"], fakulteta["ime"])
                ime = f'index_smer{i}.html'
                stran = prevedi_datoteko_v_niz(mapa, ime)
                fakulteta[f"smer{i}"] = iz_strani_profesorjov_v_profesorje(stran)


    #Strani profesorjev shranimo
    for univerza in univerze:
        for fakulteta in univerza["fakultete"]:
            for i in range(len(fakulteta["url"])):
                for profesor in fakulteta[f"smer{i}"]:
                    mapa = os.path.join(mapa_fakultet, univerza["ime_univerze"], fakulteta["ime"])
                    url = url_strani + profesor["url"]
                    ime = f'index_{profesor["ime_profesorja"]}.html'
                    if redownload:
                        shrani_stran_v_datoteko(url, mapa, ime)
                    else:
                        if not os.path.isfile(os.path.join(mapa, ime)):
                            shrani_stran_v_datoteko(url, mapa, ime)
    
    #Zgradimo seznam slovarjev, ki vsebujejo podatke vsakega profesorja
    id_num = 0 
    for univerza in univerze:
        for fakulteta in univerza["fakultete"]:
            profesorji = []
            for i in range(len(fakulteta["url"])):
                for profesor in fakulteta[f"smer{i}"]:
                    mapa = os.path.join(mapa_fakultet, univerza["ime_univerze"], fakulteta["ime"])
                    ime = f'index_{profesor["ime_profesorja"]}.html'
                    stran = prevedi_datoteko_v_niz(mapa, ime)
                    podatki_profesorja = poberi_podatke_profesorjev(stran)
                    podatki_profesorja["ime"] = profesor["ime_profesorja"]
                    podatki_profesorja["fakulteta"] = fakulteta["ime"]
                    podatki_profesorja["univerza"] = univerza["ime_univerze"]
                    podatki_profesorja["predmeti"] = podatki_profesorja["predmeti"].split(", ")
                    if podatki_profesorja["st_ocen"] == "0":
                        #Če ni ocen, potem je oceni dalo znak "-"
                        podatki_profesorja["ocena"] = 0
                        podatki_profesorja["st_ocen"] = 0
                    else:
                        podatki_profesorja["ocena"] = float(podatki_profesorja["ocena"])
                        podatki_profesorja["st_ocen"] = int(podatki_profesorja["st_ocen"])
                    #Ker nismo ločili po smereh, bi se lahko zgodilo, da bi 1 profesor poučeval na isti fakulteti na več smereh
                    preveri_ce_profesor_v_2_smereh(podatki_profesorja, profesorji)
            for profesor in profesorji:
                profesor["id"] = id_num
                id_num+=1
            tabela_profesorjev+=profesorji

    fieldnames = ["id", "ime", "fakulteta", "univerza", "predmeti", "st_ocen", "ocena"]
    zgradi_csv(fieldnames, tabela_profesorjev, mapa_podatkov_profesorjev, datoteka_podatkov_profesorjev)
    