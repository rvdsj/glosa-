import concept
import temp
import glosa_only
import math

def displayResults():

    concept_tt = []
    concept_emission = []
    rules_tt = []
    rules_emission = []
    glosa_only_tt = []
    glosa_only_emission = []
    num_runs = 5

    for x in range (0,num_runs):
        tt, co, seed=concept.sendToEval()
        concept_tt.append(tt)
        concept_emission.append(co)

        tt, co = glosa_only.sendToEval(seed)
        glosa_only_tt.append(tt)
        glosa_only_emission.append(co)

        tt, co = temp.sendToEval(seed)
        rules_tt.append(tt)
        rules_emission.append(co)

    for x in range(0,len(concept_tt)):
        print "Random flow, Glosa only, Glosa+"
        print "Travel time ",concept_tt[x], " ",glosa_only_tt[x]," ",rules_tt[x]
        print "Emission ",concept_emission[x]," ",glosa_only_emission[x], " ",rules_emission[x]


def calculate_mean_and_sd():
    concept_tt = [143,120,118,147,116,134,111,111,120,118]
    glosa_only_tt = [118,120,122,134,120,119,123,116,113,118]
    rules_tt = [118,106,108,119,102,112,98,107,117,102]

    concept_emission = [380,314,307,380,305,358,291,295,312,308]
    glosa_only_emission = [281,275,291,302,277,279,277,282,270,284]
    rules_emission = [283,258,257,268,232,253,235,265,269,249]

    acc_concept_tt = 0
    acc_glosa_only_tt = 0
    acc_rules_tt = 0

    acc_concept_emi = 0
    acc_glosa_only_emi = 0
    acc_rules_emi = 0

    num_runs = 10

    #TT

    """
    for i in range(0, len(glosa_only_tt)):
        glosa_only_tt[i]= (glosa_only_tt[i]*100)/concept_tt[i]

    for i in range(0, len(rules_tt)):
        rules_tt[i]= (rules_tt[i]*100)/concept_tt[i]
    """

    for i in range(0, len(concept_tt)):
        acc_concept_tt = acc_concept_tt + concept_tt[i]

    for i in range(0, len(glosa_only_tt)):
        acc_glosa_only_tt = acc_glosa_only_tt + glosa_only_tt[i]

    for i in range(0, len(rules_tt)):
        acc_rules_tt = acc_rules_tt + rules_tt[i]



    #emission
    """
    for i in range(0, len(glosa_only_emission)):
        glosa_only_emission[i]= (glosa_only_emission[i]*100)/concept_emission[i]

    for i in range(0, len(rules_emission)):
        rules_emission[i]= (rules_emission[i]*100)/concept_emission[i]
    """

    for i in range(0, len(concept_emission)):
        acc_concept_emi = acc_concept_emi + concept_emission[i]

    for i in range(0, len(glosa_only_emission)):
        acc_glosa_only_emi = acc_glosa_only_emi + glosa_only_emission[i]

    for i in range(0, len(rules_emission)):
        acc_rules_emi = acc_rules_emi + rules_emission[i]

    concept_mean_tt = acc_concept_tt / num_runs
    glosa_only_mean_tt = acc_glosa_only_tt / num_runs
    rules_mean_tt = acc_rules_tt / num_runs

    print "concept mean TT, glosa only mean TT , rules mean TT"
    print concept_mean_tt," ", glosa_only_mean_tt," ", rules_mean_tt
    #SD

    intermediate = 0
    for i in range(0, len(concept_tt)):
        alt = concept_tt[i] - concept_mean_tt
        intermediate = intermediate + (alt * alt)

    print "SD concept TT ", math.sqrt((1. / num_runs) * intermediate)

    intermediate = 0
    for i in range(0, len(glosa_only_tt)):
        alt = glosa_only_tt[i] - glosa_only_mean_tt
        intermediate = intermediate + (alt * alt)

    print "SD glosa only TT", math.sqrt((1. / num_runs) * intermediate)

    intermediate = 0
    for i in range(0, len(rules_tt)):
        alt = rules_tt[i] - rules_mean_tt
        intermediate = intermediate + (alt * alt)

    print "SD rules TT", math.sqrt((1. / num_runs) * intermediate)

    concept_mean_emi = acc_concept_emi / num_runs
    glosa_only_mean_emi = acc_glosa_only_emi / num_runs
    rules_mean_emi = acc_rules_emi / num_runs

    print "concept mean emi, glosa only mean emi, rules mean emi"
    print concept_mean_emi, " ", glosa_only_mean_emi, " ", rules_mean_emi

    intermediate = 0
    for i in range(0, len(concept_emission)):
        alt = concept_emission[i] - concept_mean_emi
        intermediate = intermediate + (alt * alt)

    print "SD concept emi",math.sqrt((1. / num_runs) * intermediate)

    intermediate = 0
    for i in range(0, len(glosa_only_emission)):
        alt = glosa_only_emission[i] - glosa_only_mean_emi
        intermediate = intermediate + (alt * alt)

    print "SD glosa only emi",math.sqrt((1. / num_runs) * intermediate)

    intermediate = 0
    for i in range(0, len(rules_emission)):
        alt = rules_emission[i] - rules_mean_emi
        intermediate = intermediate + (alt * alt)

    print "SD rules emi", math.sqrt((1. / num_runs) * intermediate)

if __name__ == '__main__':
    #displayResults()
    calculate_mean_and_sd()