from pathlib import Path
import json

# Загрузка данных
path_to_roots = Path("roots.json")
with open(path_to_roots, 'r') as file:
    roots = json.load(file)

path_to_alias = Path("alias_key.json")
with open(path_to_alias, 'r') as file:
    pango_alias = json.load(file)

# Удаление ненужных ключей
del pango_alias["A"]
del pango_alias["B"]

# Обратный словарь alias
pango_alias_reverse = {j: i for i, j in pango_alias.items() if type(j) == str}

roots_corrected = {}
for i in roots:
    try:
        roots_corrected[pango_alias_reverse[i]] = roots[i].replace(roots[i].split(" ")[0], pango_alias_reverse[i]+"*")
    except:
        roots_corrected[i] = roots[i]

def strain_to_fullpango(strain: str):
    strain = strain.upper()
    if strain.split(".")[0] not in pango_alias:
        return strain
    if type(pango_alias[strain.split(".")[0]]) == list:
        return strain
    else:
        if strain.split(".")[0] in pango_alias:
            fullstrain = strain.replace(strain.split(".")[0], pango_alias[strain.split(".")[0]])
            #print(fullstrain)
            fullstrain_old = fullstrain
            flag=True
            if flag:
                try:
                    fullstrain = strain_to_fullpango(strain=fullstrain)
                except:
                    flag=False
                if fullstrain == fullstrain_old:
                    flag=False
            return fullstrain
        else:
            return strain

def create_path_to_root(fullstrain: str):
    path_to_root = []
    for i in range(len(fullstrain.split("."))):
        if i == 0:
            path_to_root.append(fullstrain)
        else:
            parent = ".".join(fullstrain.split(".")[:-i])
            path_to_root.append(parent)
    return path_to_root

def fullpango_to_strain(fullpango: str):
    variants_of_collapsing = []
    for strain in pango_alias_reverse:
        collapse = fullpango.replace(strain, pango_alias_reverse[strain])
        variants_of_collapsing.append(collapse)
    result = min(variants_of_collapsing, key=lambda x: len(x))
    return result

def final_collapsed_strain(collapsed_path):
    res = collapsed_path[0]
    for strain in collapsed_path:
        if strain in roots_corrected:
            res = strain
            break
    try:
        return roots_corrected[res]
    except:
        return "Other"

def create_collapsed_strain(strain):
    fullpango = strain_to_fullpango(strain)
    path_to_root = create_path_to_root(fullpango)
    collapsed_path = [fullpango_to_strain(i) for i in path_to_root]
    return final_collapsed_strain(collapsed_path)