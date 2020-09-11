from glob import glob
from PIL import Image
from PIL.ImageOps import grayscale, colorize
from pathlib import Path
from collections import defaultdict

import os
import json


def image_tint(src, tint='#ffffff'):
    src = Image.open(src).convert('RGBA')
    r, g, b, alpha = src.split()
    gray = grayscale(src)
    result = colorize(gray, (0, 0, 0, 0), tint)
    result.putalpha(alpha)
    return result


def clean(string):
    return " ".join([word.capitalize() for word in string.split('_')])


def gen_name(ty):
    id = ty.id

    lang_json = {}
    with open('src/main/resources/assets/modern_industrialization/lang/en_us.json', 'r') as lang_file:
        lang_json = json.load(lang_file)
        lang_file.close()

    for item in ty.mi_items:
        lang_id = 'item.modern_industrialization.' + (id + '_' + item)
        name = clean(id) + " " + clean(item)
        lang_json[lang_id] = name

    if 'fluid_pipe' in ty.overrides:
        lang_json['item.modern_industrialization.pipe_fluid_' +
                  id] = clean(id) + ' Fluid Pipe'
    if 'item_pipe' in ty.overrides:
        lang_json['item.modern_industrialization.pipe_item_' +
                  id] = clean(id) + ' Item Pipe'
    if 'cable' in ty.overrides:
        lang_json['item.modern_industrialization.pipe_electricity_' +
                  id] = clean(id) + ' Cable'

    for block in ty.mi_blocks:
        lang_id = 'block.modern_industrialization.' + (id + '_' + block)
        name = clean(id) + " " + clean(block)
        lang_json[lang_id] = name

    with open('src/main/resources/assets/modern_industrialization/lang/en_us.json', 'w') as lang_file:
        json.dump(lang_json, lang_file, indent=4, sort_keys=True)
        lang_file.close()


def gen_texture(id, hex, item_set, block_set, special_texture=''):

    item = glob("template/item/*.png")

    output_path = (
        "src/main/resources/assets/modern_industrialization/textures/items/materials/" + id)
    Path(output_path).mkdir(parents=True, exist_ok=True)

    for filename in item:
        t = os.path.basename(filename).split('.')[0]
        if t in item_set:
            print(filename)
            result = image_tint(filename, hex)
            if t in TEXTURE_UNDERLAYS:
                underlay = Image.open("template/item/%s_underlay.png" % t)
                result = Image.alpha_composite(underlay, result)
            if t in TEXTURE_OVERLAYS:
                overlay = Image.open("template/item/%s_overlay.png" % t)
                result = Image.alpha_composite(result, overlay)
            if t != special_texture:
                result.save(output_path + '/' + os.path.basename(filename))
            else:
                result.save(output_path + '/' + t + ".png")

    block = glob("template/block/*.png")
    output_path = "src/main/resources/assets/modern_industrialization/textures/blocks/materials/" + id
    Path(output_path).mkdir(parents=True, exist_ok=True)

    for filename in block:
        t = os.path.basename(filename).split('.')[0]
        if t in block_set:
            result = image_tint(filename, hex)
            if t in TEXTURE_UNDERLAYS:
                underlay = Image.open("template/block/%s_underlay.png" % t)
                result = Image.alpha_composite(underlay, result)
            if t in TEXTURE_OVERLAYS:
                overlay = Image.open("template/block/%s_overlay.png" % t)
                result = Image.alpha_composite(result, overlay)
            result.save(output_path + '/' + os.path.basename(filename))

loaded_items = {'modern_industrialization:rubber_sheet'}

# check if the item json is valid based on the loaded items


def allow_recipe(jsonf):
    if "item" not in jsonf:
        return True
    namespace, _ = jsonf["item"].split(":")
    return namespace == "minecraft" or jsonf["item"] in loaded_items


class MIRecipe:

    def __init__(self, type, eu=2, duration=200):
        self.type = type
        self.eu = eu
        self.duration = duration

    def __ensure_list(self, attr):
        if not hasattr(self, attr):
            setattr(self, attr, [])

    def input(self, input, amount=1):
        self.__ensure_list("item_inputs")
        input_json = get_input_json(input)
        input_json["amount"] = amount
        self.item_inputs.append(input_json)
        return self

    def fluid_input(self, fluid, amount):
        self.__ensure_list("fluid_inputs")
        self.fluid_inputs.append({"fluid": fluid, "amount": amount})
        return self

    def output(self, item, amount=1):
        self.__ensure_list("item_outputs")
        self.item_outputs.append({"item": item, "amount": amount})
        return self

    def fluid_output(self, fluid, amount):
        self.__ensure_list("fluid_outputs")
        self.fluid_outputs.append({"fluid": fluid, "amount": amount})
        return self

    def save(self, id, suffix):
        path = "src/main/resources/data/modern_industrialization/recipes/generated/materials/" + \
            id + "/" + self.type + "/"
        Path(path).mkdir(parents=True, exist_ok=True)

        allowed = True
        jsonf = {"type": "modern_industrialization:" +
                 self.type, "eu": self.eu, "duration": self.duration}
        optionals = ["item_inputs", "fluid_inputs",
                     "item_outputs", "fluid_outputs"]
        for opt in optionals:
            if hasattr(self, opt):
                inputs = []
                for i in getattr(self, opt):
                    allowed = allowed and allow_recipe(i)
                    inputs.append(i)
                jsonf[opt] = inputs
        if allowed:
            with open(path + suffix + ".json", "w") as file:
                json.dump(jsonf, file, indent=4)


def get_input_json(string):
    return {"tag": string[1:]} if string[0] == '#' else {"item": string}


class CraftingRecipe:

    def __init__(self, pattern, output, count=1, **kwargs):
        self.pattern = pattern
        self.output = output
        self.count = count
        self.kwargs = kwargs

    def save(self, id, suffix):
        path = "src/main/resources/data/modern_industrialization/recipes/generated/materials/" + id + "/craft/"
        Path(path).mkdir(parents=True, exist_ok=True)
        jsonf = {"type": "minecraft:crafting_shaped", "pattern": self.pattern,
                 "result": {"item": self.output, "count": self.count}}
        keys = {}
        allowed = allow_recipe(jsonf["result"])
        for line in self.pattern:
            for c in line:
                if c != " ":
                    keys[c] = get_input_json(self.kwargs[c])
                    allowed = allowed and allow_recipe(keys[c])
        jsonf["key"] = keys
        if allowed:
            with open(path + suffix + ".json", "w") as file:
                json.dump(jsonf, file, indent=4)
        return self

    def export(self, other_type, id, suffix, **kwargs):  # will also save
        recipe = MIRecipe(other_type, **kwargs)
        recipe.output(self.output, self.count)
        keycount = defaultdict(lambda: 0)
        keys = {}
        for line in self.pattern:
            for c in line:
                if c != " ":
                    keys[c] = {"tag": self.kwargs[c][1:]} if self.kwargs[
                        c][0] == '#' else {"item": self.kwargs[c]}
                    keycount[c] += 1
        for k in keys:
            recipe.input("#" + keys[k]["tag"] if "tag" in keys[k]
                         else keys[k]["item"], amount=keycount[k])
        recipe.save(id, suffix)


def genForgeHammer(ty, tyo):
    hammer = "forge_hammer_hammer"
    saw = "forge_hammer_saw"

    list_todo = [('large_plate', 1, 'curved_plate', 3, hammer),
                 ('double_ingot', 1, 'plate', 1, hammer),
                 ('nugget', 1, 'small_dust', 1, hammer),
                 ('main', 1, 'rod', 1, saw),
                 ('large_plate', 1, 'gear', 1, saw),
                 ('rod', 1, 'bolt', 1, saw),
                 ('ore', 1, 'crushed_dust', 2, hammer),
                 ('pipe_item', 1, 'ring', 1, saw),
                 ('main', 2, 'double_ingot', 1, hammer),
                 ]

    for a, inputCount, b, c, d in list_todo:
        MIRecipe(d).input(tyo[a], inputCount).output(ty[b], c).save(ty.id, b)


def genCraft(vanilla, ty):
    list_full = [('small_dust', 'dust')]

    if not vanilla:
        list_full.append(('nugget', 'main'))
        list_full.append(('main', 'block'))

    for (a, b) in list_full:
        CraftingRecipe(
            ["xxx", "xxx", "xxx"],
            ty[b],
            x=ty[a],
        ).save(ty.id, "%s_from_%s" % (b, a))
        CraftingRecipe(
            ["x"],
            ty[a],
            9,
            x=ty[b],
        ).save(ty.id, "%s_from_%s" % (a, b))

    CraftingRecipe([
        "P",
        "P",
        "I"
    ],
        ty["blade"],
        4,
        P=ty["plate"],
        I=ty["rod"],
    ).save(ty.id, "blade").export("assembler", ty.id, "blade", eu=8)

    CraftingRecipe([
        "PPP",
        "P P",
        "PPP"
    ],
        ty["machine_casing"],
        1,
        P=ty["large_plate"],
    ).save(ty.id, "machine_casing").export("assembler", ty.id, "machine_casing", eu=8)

    CraftingRecipe([
        "PPP",
        "P P",
        "PPP"
    ],
        ty["coil"],
        1,
        P=ty["wire"],
    ).save(ty.id, "coil").export("assembler", ty.id, "coil", eu=8)

    CraftingRecipe([
        "PP",
        "PP"
    ],
        ty["large_plate"],
        P=ty["plate"],
    ).save(ty.id, "large_plate").export("packer", ty.id, "large_plate")

    CraftingRecipe([
        "bBb",
        "BRB",
        "bBb"
    ],
        ty["rotor"],
        b=ty["bolt"],
        B=ty["blade"],
        R=ty["ring"],
    ).save(ty.id, "rotor").export("assembler", ty.id, "rotor", eu=8)

    CraftingRecipe([
        "ppp",
        "   ",
        "ppp",
    ],
        ty["item_pipe"],
        6,
        p=ty["curved_plate"],
    ).save(ty.id, "item_pipe").export("packer", ty.id, "item_pipe")

    CraftingRecipe([
        "ppp",
        "ggg",
        "ppp",
    ],
        ty["fluid_pipe"],
        6,
        g="minecraft:glass_pane",
        p=ty["curved_plate"],
    ).save(ty.id, "fluid_pipe")

    CraftingRecipe([
        "rrr",
        "www",
        "rrr",
    ],
        ty["cable"],
        3,
        r="modern_industrialization:rubber_sheet",
        w=ty["wire"],
    ).save(ty.id, "cable").export("assembler", ty.id, "cable", eu=8)


def genSmelting(vanilla, ty, isMetal):
    path = "src/main/resources/data/modern_industrialization/recipes/generated/materials/" + \
        ty.id + "/smelting/"
    Path(path).mkdir(parents=True, exist_ok=True)

    list_todo = [('small_dust', 'nugget', 0.08),
                 ('crushed_dust', 'main', 0.7),  ('dust', 'main', 0.7)]

    if not vanilla:
        list_todo.append(('ore', 'main', 0.7))

    for a, b, c in list_todo:
        if ty[a] in loaded_items and ty[b] in loaded_items:
            list_recipe = [("smelting", 200)]
            if isMetal:
                list_recipe.append(('blasting', 100))
            for d, e in list_recipe:
                jsonf = {}
                jsonf["type"] = "minecraft:" + d
                jsonf["ingredient"] = {"item": ty[a]}
                jsonf["result"] = ty[b]
                jsonf["experience"] = c
                jsonf["cookingtime"] = e
                with open(path + "/" + a + "_" + d + ".json", "w") as file:
                    json.dump(jsonf, file, indent=4)


def genMacerator(ty, tyo):
    list_todo = [('double_ingot', 18), ('plate', 9), ('curved_plate', 9),
                 ('nugget', 1), ('large_plate', 36), ('gear', 18), ('ring', 4),
                 ('bolt', 2), ('rod', 4), ('item_pipe', 9), ('fluid_pipe', 9),
                 ('rotor', 27), ('main', 9)]
    for a, b in list_todo:
        recipe = MIRecipe('macerator').input(tyo[a])
        if b // 9 != 0:
            recipe.output(ty["dust"], b // 9)
        if b % 9 != 0:
            recipe.output(ty["small_dust"], b % 9)
        recipe.save(ty.id, a)

    MIRecipe("macerator").input(tyo["ore"]).output(
        ty["crushed_dust"], amount=2).save(ty.id, "ore")
    MIRecipe("macerator").input(ty["crushed_dust"], amount=2).output(
        ty["dust"], amount=3).save(ty.id, "crushed_dust")


def genCompressor(ty, tyo):
    for a, b, c in [('main', 'plate', 1), ('plate', 'curved_plate', 1), ('double_ingot', 'plate', 2)]:
        MIRecipe("compressor").input(tyo[a]).output(
            ty[b], amount=c).save(ty.id, a)


def genCuttingSaw(ty, tyo):
    for a, b, c in [('main', 'rod', 2), ('rod', 'bolt', 2), ('large_plate', 'gear', 2), ('item_pipe', 'ring', 2)]:
        MIRecipe("cutting_machine").input(tyo[a]).fluid_input(
            'minecraft:water', amount=1).output(ty[b], amount=c).save(ty.id, a)


def genPacker(ty, tyo):
    MIRecipe("packer").input(ty["main"], amount=2).output(
        ty["double_ingot"]).save(ty.id, "double_ingot")
    MIRecipe("packer").input(ty["item_pipe"], amount=2).input(
        "minecraft:glass_pane").output(ty["fluid_pipe"], amount=2).save(ty.id, "fluid_pipe")


def genWiremill(ty, tyo):
    for i, ic, o, oc in [('plate', 1, 'wire', 2), ('wire', 1, 'fine_wire', 4)]:
        MIRecipe("wiremill").input(tyo[i], amount=ic).output(
            ty[o], amount=oc).save(ty.id, o)

material_lines = []


def gen(file, ty, hex, vanilla=False, forge_hammer=False, smelting=True, isMetal=True, veinsPerChunk=0, veinsSize=0, maxYLevel=64, texture=''):

    item_to_add = ','.join([(lambda s: "\"%s\"" % s)(s)
                            for s in sorted(list(ty.mi_items))])

    line = "    public static MIMaterial %s = new MIMaterial(\"%s\", %s)" % (
        ty.id, ty.id, ("%s" % vanilla).lower())

    line += ".addItemType(new String [] { %s})" % item_to_add

    if len(ty.mi_blocks) > 0:
        block_to_add = ','.join([(lambda s: "\"%s\"" % s)(s)
                                 for s in sorted(list(ty.mi_blocks))])
        line += ".addBlockType(new String [] { %s })" % block_to_add

    if 'ore' in ty.mi_blocks:
        line += '.setupOreGenerator(%d, %d, %d)' % (veinsPerChunk,
                                                    veinsSize, maxYLevel)

    gen_name(ty)

    line += ';'
    global material_lines
    material_lines.append(line)

    print(line)

    gen_texture(ty.id, hex, ty.mi_items, ty.mi_blocks)

    tyo = ty.get_oredicted()

    if forge_hammer:
        genForgeHammer(ty, tyo)

    genCraft(vanilla, ty)

    if smelting:
        genSmelting(vanilla, ty, isMetal)

    genMacerator(ty, tyo)
    genCompressor(ty, tyo)
    genCuttingSaw(ty, tyo)
    genPacker(ty, tyo)
    genWiremill(ty, tyo)


BLOCK_ONLY = {'block'}
BLOCK_CASING = {'block', 'machine_casing'}
ORE_ONLY = {'ore'}
BOTH = {'block', 'ore'}

ITEM_BASE = {'ingot', 'plate', 'large_plate', 'nugget', 'double_ingot',
             'small_dust', 'dust', 'curved_plate', 'crushed_dust'}  # TODO: pipes

PURE_METAL = {'ingot', 'nugget', 'small_dust', 'dust', 'crushed_dust'}
PURE_NON_METAL = {'small_dust', 'dust', 'crushed_dust'}

ITEM_ALL = ITEM_BASE | {'bolt', 'blade',
                        'ring', 'rotor', 'gear', 'rod'}

ITEM_ALL_NO_ORE = ITEM_ALL - {'crushed_dust'}
TEXTURE_UNDERLAYS = {'ore'}
TEXTURE_OVERLAYS = {'fine_wire'}
DEFAULT_OREDICT = {'main': '_ingots', 'nugget': '_nuggets', 'ore': '_ores'}
RESTRICTIVE_OREDICT = {'ore': '_ores'}


class Material:

    def __init__(self, id, mi_items, mi_blocks, overrides={}, oredicted={}):
        self.id = id
        self.mi_items = mi_items
        self.mi_blocks = mi_blocks
        if "ingot" in mi_items:
            overrides["main"] = "modern_industrialization:" + id + "_ingot"
            if oredicted == {}:
                oredicted = DEFAULT_OREDICT
        self.overrides = overrides
        self.oredicted = oredicted
        self.__load()

    def __load(self):
        global loaded_items
        for item in self.mi_items | self.mi_blocks:
            loaded_items |= {
                "modern_industrialization:" + self.id + "_" + item}
        for ov in self.overrides.values():
            loaded_items |= {ov}
        return self

    def get_oredicted(self):
        class OredictedMaterial:

            def __init__(self, outer):
                self.outer = outer

            def __getitem__(self, item):
                if item in self.outer.oredicted:
                    return '#c:' + self.outer.id + self.outer.oredicted[item]
                else:
                    return self.outer[item]

        return OredictedMaterial(self)

    def __getitem__(self, item):
        return "modern_industrialization:" + self.id + "_" + item if item not in self.overrides else self.overrides[item]


if __name__ == '__main__':
    file = open(
        "src/main/java/aztech/modern_industrialization/material/MIMaterials.java", "w")
    file.write("""package aztech.modern_industrialization.material;

public class MIMaterials {

""")
    file.close()
    file = open(
        "src/main/java/aztech/modern_industrialization/material/MIMaterials.java", "a")

    gen(
        file,
        Material('gold', ITEM_BASE - {'ingot', 'nugget'}, set(), overrides={
            "main": "minecraft:gold_ingot",
            "nugget": "minecraft:gold_nugget",
            "ore": "minecraft:gold_ore",
            "item_pipe": "modern_industrialization:pipe_item_gold",
            "fluid_pipe": "modern_industrialization:pipe_fluid_gold",
        }),
        '#ffe100', vanilla=True,
    )
    gen(
        file,
        Material('iron', ITEM_BASE - {'ingot', 'nugget'}, set(), overrides={
            "main": "minecraft:iron_ingot",
            "nugget": "minecraft:iron_nugget",
            "ore": "minecraft:iron_ore",
            "item_pipe": "modern_industrialization:pipe_item_iron",
            "fluid_pipe": "modern_industrialization:pipe_fluid_iron",
        }),
        '#f0f0f0', vanilla=True, forge_hammer=True,
    )
    gen(
        file,
        Material('coal', PURE_NON_METAL, set(), overrides={
            "main": "minecraft:coal",
            "ore": "minecraft:coal_ore",
        }),
        '#282828', vanilla=True, forge_hammer=True, isMetal=False, smelting=False,
    )
    gen(
        file,
        Material('copper', ITEM_ALL | {'wire', 'fine_wire'}, BOTH, overrides={
            "item_pipe": "modern_industrialization:pipe_item_copper",
            "fluid_pipe": "modern_industrialization:pipe_fluid_copper",
            "cable": "modern_industrialization:pipe_electricity_copper",
        }),
        '#ff6600', forge_hammer=True, veinsPerChunk=20, veinsSize=9, maxYLevel=128,
    )
    gen(
        file,
        Material('bronze', ITEM_ALL_NO_ORE, BLOCK_CASING, overrides={
            "item_pipe": "modern_industrialization:pipe_item_bronze",
            "fluid_pipe": "modern_industrialization:pipe_fluid_bronze",
        }),
        '#ffcc00', forge_hammer=True,
    )
    gen(
        file,
        Material('tin', ITEM_ALL | {'wire'}, BOTH, overrides={
            "item_pipe": "modern_industrialization:pipe_item_tin",
            "fluid_pipe": "modern_industrialization:pipe_fluid_tin",
            "cable": "modern_industrialization:pipe_electricity_tin",
        }),
        '#cbe4e4', forge_hammer=True, veinsPerChunk=8, veinsSize=9,
    )
    gen(
        file,
        Material('steel', ITEM_ALL_NO_ORE, BLOCK_CASING, oredicted=RESTRICTIVE_OREDICT, overrides={
            "item_pipe": "modern_industrialization:pipe_item_steel",
            "fluid_pipe": "modern_industrialization:pipe_fluid_steel",
        }),
        '#3f3f3f',
    )
    gen(
        file,
        Material('aluminum', ITEM_BASE | {'ingot'}, BLOCK_CASING, oredicted={'nope'}, overrides={
            "item_pipe": "modern_industrialization:pipe_item_aluminum",
            "fluid_pipe": "modern_industrialization:pipe_fluid_aluminum",
        }),
        '#3fcaff', smelting=False,
    )
    gen(
        file,
        Material('bauxite', PURE_NON_METAL, ORE_ONLY),
        '#cc3908', isMetal=False, smelting=False, veinsPerChunk=8, veinsSize=7, maxYLevel=32,
    )
    gen(
        file,
        Material('lignite_coal', PURE_NON_METAL | {'lignite_coal'}, ORE_ONLY, overrides={
            'main': 'modern_industrialization:lignite_coal',
        }),
        '#604020', forge_hammer=True, isMetal=False, veinsPerChunk=20, veinsSize=17, maxYLevel=128,
    )
    gen(
        file,
        Material('lead', ITEM_BASE, BOTH, overrides={
            "item_pipe": "modern_industrialization:pipe_item_lead",
            "fluid_pipe": "modern_industrialization:pipe_fluid_lead",
        }),
        '#4a2649', veinsPerChunk=4, veinsSize=8, maxYLevel=64,
    )
    gen(
        file,
        Material('battery_alloy', {'small_dust', 'dust',
                                   'plate', 'nugget', 'curved_plate', 'ingot',
                                   'double_ingot'}, BLOCK_ONLY),
        '#a694a5',
    )
    gen(
        file,
        Material('invar', {'small_dust', 'dust', 'plate',
                           'ingot', 'double_ingot', 'nugget', 'large_plate', 'gear'}, BLOCK_CASING, oredicted={'nope'}),
        '#b4b478',
    )

    gen(
        file,
        Material('cupronickel', {'small_dust', 'dust', 'plate',
                                 'ingot', 'nugget', 'wire', 'double_ingot'}, BLOCK_ONLY | {'coil'}, oredicted={'nope'}),
        '#e39680',
    )

    gen(
        file,
        Material('antimony', PURE_METAL, BOTH),
        '#91bdb4', veinsPerChunk=4, veinsSize=6, maxYLevel=64,
    )
    gen(
        file,
        Material('nickel', ITEM_BASE, BOTH, overrides={
            "item_pipe": "modern_industrialization:pipe_item_nickel",
            "fluid_pipe": "modern_industrialization:pipe_fluid_nickel",
        }),
        '#a9a9d4', veinsPerChunk=7, veinsSize=6, maxYLevel=64,
    )
    gen(
        file,
        Material('silver', ITEM_BASE, BOTH, overrides={
            "item_pipe": "modern_industrialization:pipe_item_silver",
            "fluid_pipe": "modern_industrialization:pipe_fluid_silver",
        }),
        '#99ffff', veinsPerChunk=4, veinsSize=6, maxYLevel=64,
    )

    file.write("\n".join(sorted(material_lines)))
    file.write("\n")
    file.write("}")
    file.close()

print(loaded_items)
