import csv
import matplotlib.pyplot as pyplt
import string

# 
# Questions
#    1. should we count and visualize skips?
#    2. Should skip color be same in all plots?
#    2.5 Should skip be in order or at end?
#    3. What is the "ideal" for each bit of data?
#    4. "Asian" is such a poor label
#    5. We don't have "White or Caucasion" but do have
#          "Black or African American"
#          "Hispanic or Latino"
#          "Middle Eastern or North African"
#    6. For underrepresented description, how should we
#       handle intersectional responses?
#    7. Should the visualizations aggregate smaller
#       categories to an "other"


#
# Education labels are really, really long.
# We'll shorten them here to some abbreviations.
#
def adjustEducation(pdb):
    for i in range(len(pdb['labels'])):
        if pdb['labels'][i].startswith('Doctorate'):
            pdb['labels'][i] = 'PhD'
        elif pdb['labels'][i].startswith('Master'):
            pdb['labels'][i] = 'MS'
        elif pdb['labels'][i].startswith('Bachelor'):
            pdb['labels'][i] = 'BS'
        elif pdb['labels'][i].startswith('Associate'):
            pdb['labels'][i] = 'BA'
        elif pdb['labels'][i].startswith('Completed secondary'):
            pdb['labels'][i] = 'HS/GED'
        elif pdb['labels'][i].startswith('Incomplete secondary'):
            pdb['labels'][i] = 'GS'

#
# For country names with spaces in them, take only 
# first letters from each upper case word.
#
def adjustCountry(pdb):
    for i in range(len(pdb['labels'])):
        if not ' ' in pdb['labels'][i]:
            continue
        words = pdb['labels'][i].split() 
        letters = ''.join([word[0] for word in words if word[0].isupper()])
        pdb['labels'][i] = letters

#
# Career stage labels are a bit long too.
# Lets trim them down a bit.
#
def adjustCareerStage(pdb):
    for i in range(len(pdb['labels'])):
        if pdb['labels'][i].startswith('More than 15'):
            pdb['labels'][i] = '>15yrs'
        elif pdb['labels'][i].startswith('From 7 to 15'):
            pdb['labels'][i] = '7-15yrs'
        elif pdb['labels'][i].startswith('Less than 7'):
            pdb['labels'][i] = '<7yrs'

#
# There is a lot to do here...
#     For intersectional, we should count in all bins listed
#         eg. Latin-american women means count once in latinx and once in women
#     Merge synonymous labels and sizes
#     Reduce label lengths
#     Best solution is probably to aprior define possible labels and then
#     map each term in free text to one of the apriori labels and warn if
#     a term doesn't match anywhere.
#
def adjustUnderrepresentedDesc(pdb):
    return # punting for now

def adjustRace(pdb):
    for i in range(len(pdb['labels'])):
        if pdb['labels'][i].startswith('Hispanic'):
            pdb['labels'][i] = 'Latinx'
        elif pdb['labels'][i].startswith('Black'):
            pdb['labels'][i] = 'Black'
        elif pdb['labels'][i].startswith('Middle'):
            pdb['labels'][i] = 'MENA'

def adjustLabelsAndSizes(blockName, pieDataBlock):

    if blockName == "Education":
        adjustEducation(pieDataBlock)
    elif blockName == "Residence Country":
        adjustCountry(pieDataBlock)
    elif blockName == "Nationality":
        adjustCountry(pieDataBlock)
    elif blockName == "Career Stage":
        adjustCareerStage(pieDataBlock)
    elif blockName == "Underrepresented Desc":
        adjustUnderrepresentedDesc(pieDataBlock)
    elif blockName == "Race":
        adjustRace(pieDataBlock)

#
# Here is what a new block looks like in the file...
#
#     demographics_age_group  What is your age group? (private)
#     total_responders        166
#     total_no_response       3
#     total_responses 213 (optional)
#     (blank)
#     .
#     .
#     .
#
def processNewBlock(i, lines, pieData):

    # Get Block title and question
    item = lines[i]
    n = item['item_name'][13:].replace('_',' ')
    blockName = string.capwords(n)
    q = item['item_value1']
    blockQuestion = string.capwords(q[0:q.find('?')+1])
    i += 1

    # get total responders to block
    totalResponders = -1
    item = lines[i]
    if item['item_name'] == "total_responders":
        totalResponders = int(item['item_value1'])
        i += 1

    # get total no responses to block
    totalNoResponses = -1
    item = lines[i]
    if item['item_name'] == "total_no_response":
        totalNoResponses = int(item['item_value1'])
        i += 1

#    print('New block title = "%s"'%blockName)
#    print('    question = "%s"'%blockQuestion)
#    print('    total responders = %d'%totalResponders)
#    print('    total no responses = %d'%totalNoResponses)

    if i >= len(lines):
        return i

    totalResponses = -1
    item = lines[i]
    if item['item_name'] == "total_responses":
        totalResponses = int(item['item_value1'])
        i += 1

    pieData[blockName] = {}

    if i >= len(lines):
        return i

    labels = []
    sizes = []
    total = 0
    while i < len(lines) and not lines[i]['item_name'].startswith("demographics_"):
        item = lines[i]
        label = item['item_name'].replace("Prefer not to submit","Skip")
        labels += [label]
        sizes += [int(item['item_value2'])]
        total += int(item['item_value2'])
        i += 1

    # Move "Skip" category, if any, to the end
    try:
        i = labels.index('Skip')
        s = sizes[i]
        l = labels[i]
        del(labels[i]) 
        del(sizes[i])
        sizes += [s]
        labels += [l]
    except:
        pass
    
    pieData[blockName]['labels'] = labels
    pieData[blockName]['sizes'] = sizes
    pieData[blockName]['question'] = blockQuestion
    pieData[blockName]['totrespd'] = totalResponders
    pieData[blockName]['totnoresp'] = totalNoResponses
    pieData[blockName]['totresps'] = totalResponses

    adjustLabelsAndSizes(blockName, pieData[blockName])

    return i-1

def slidePlots(piePlots,nR,nC,tit,tot,pg):
    keys = list(piePlots.keys())
    fig, axs = pyplt.subplots(nR,nC)
    fig.set_size_inches(16,9)
    fig.suptitle('%s (%d)'%(tit,tot),fontsize=24)
    for i in range(nR):
        for j in range(nC):
            if i*nC+j >= len(piePlots):
                fig.delaxes(axs[i][j])
                continue
            k = keys[i*nC+j]
#            axs[i][j].pie(piePlots[k]['sizes'], labels=piePlots[k]['labels'], autopct='%1.1f%%', shadow=False, startangle=60, pctdistance=0.75)
#            axs[i][j].axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
            y_pos = range(len(piePlots[k]['labels']))
            print(y_pos, piePlots[k]['sizes'])
            axs[i][j].barh(y_pos, piePlots[k]['sizes'])
            axs[i][j].set_yticks(y_pos, labels=piePlots[k]['labels'])
            axs[i][j].set_title('%s (%d)'%(k,piePlots[k]['totrespd']))
    #pyplt.show()
    fn = tit.lower().replace(' ','-')
    pyplt.savefig('%s-%d'%(fn,pg),dpi=300)

#
# This is what header info looks like
#     dataset_name    SC23 Committee
#     dataset_size    169
#     total_responded_to_any  166
#     total_not_responded     3
#
def getHeaderInfo(lines):
    title = None
    size = None
    nr = None
    for i in range(4):

        item = lines[i]

        # get dataset title
        if not title and item['item_name'] == "dataset_name":
            title = item['item_value1']
            continue

        # get dataset size
        if not size and item['item_name'] == "dataset_size":
            size = int(item['item_value1'])
            continue

        # get non responded count
        if not nr and item['item_name'] == "total_non_responded":
            nr = int(item['item_value1'])
            continue

    return title, size, nr

#with open('SC23_demographic_data-fall-2022.tsv', 'r', encoding='utf8') as demo_file:
with open('SC23_demographic_data-fall-2022.tsv', 'r') as demo_file:
#with open('bar.txt', 'r') as demo_file:
    tsv_reader = csv.DictReader(demo_file, delimiter="\t")
    lines = []
    for item in tsv_reader:
        lines += [item]
    hdrTitle, totSize, totNoResp = getHeaderInfo(lines[0:6])
    pieData = {}
    for i in range(len(lines)):
        item = lines[i]
        if item['item_name'].startswith("demographics_"):
            i = processNewBlock(i, lines, pieData)
        if i >= len(lines):
            break
    #
    # Plot data 2x2 (4 at a time)
    #
    page = 1
    for i in range(0, len(pieData.keys()), 4):
        piePlots = {k:pieData[k] for k in list(pieData.keys())[i:i+4]}
        slidePlots(piePlots,2,2,hdrTitle,totSize,page)
        page += 1
