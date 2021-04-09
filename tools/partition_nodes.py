from hostlist import expand_hostlist, collect_hostlist
import random

# from partition "normal"
mc_nodes="nid[00004-00007,00012-00024,00026-00062,00064-00067,00072-00126,00128-00190,00192-00195,00200-00254,00260-00318,00320-00323,00328-00382,00388-00446,00456-00510,00516-00574,00576-00579,00584-00638,00644-00702,00704-00707,00712-00766,00772-00830,00832-00835,00840-00894,00900-00958,00960-00963,00968-01022,01028-01086,01088-01150,01152-01192,01194-01214,01216-01278,01280-01723]"

gpu_nodes="nid[01928-01935,01940-01967,01972-02319,02324-02351,02356-02703,02708-02735,02740-03087,03092-03119,03124-03471,03476-03503,03512-03855,03860-03887,03892-04239,04244-04271,04280-07679]"


exp_mc = expand_hostlist(mc_nodes)
exp_gpu = expand_hostlist(gpu_nodes)
total_mc = len(exp_mc)
total_gpu = len(exp_gpu)


print("# MC nodes: %d" % (total_mc))
print("# GPU nodes: %d" % (total_gpu))

ci=[ 'pt_em', 'pt_eth', 'pt_mr', 'pt_u', 'pa_pr', 'pa_ul', 'pa_rest', 'ce_ich', 'ce_uzh' ]
ci_mc=[  1/8, 1/8, 1/8, 1/8, 0.0, 1/8, 1/8, 1/8, 1/8 ]
ci_gpu=[ 0.0, 1/4, 0.0, 0.0, 1/4, 1/4, 1/4, 0.0, 0.0 ]

ci_nnodes=dict()
rest_mc=0
rest_gpu=0
for idx, c in enumerate(ci):
    n_gpu = int(ci_gpu[idx]*total_gpu)
    rest_gpu+=n_gpu
    n_mc = int(ci_mc[idx]*total_mc)
    rest_mc+=n_mc
    ci_nnodes[c]=[ n_gpu, n_mc ]

rest_gpu = total_gpu - rest_gpu
rest_mc = total_mc - rest_mc
print("rest: ",rest_gpu, rest_mc)

if rest_gpu != 0:
    k = random.choice(list(ci_nnodes.keys()))
    while ci_nnodes[k][0] == 0:
        k = random.choice(list(ci_nnodes.keys()))
    ci_nnodes[k][0]+=rest_gpu
if rest_mc != 0:
    k = random.choice(list(ci_nnodes.keys()))
    while ci_nnodes[k][1] == 0:
        k = random.choice(list(ci_nnodes.keys()))
    ci_nnodes[k][1]+=rest_mc
print(ci_nnodes)

start_gpu=0
start_mc=0
ci_nodelist=dict()
for k in ci_nnodes:
    n_gpu, n_mc = ci_nnodes[k]
    nodelist_gpu=[]
    nodelist_mc=[]
    if n_gpu > 0:
        nodelist_gpu=exp_gpu[start_gpu:start_gpu+n_gpu]
        start_gpu+=n_gpu
    if n_mc > 0:
        nodelist_mc=exp_mc[start_mc:start_mc+n_mc]
        start_mc+=n_mc
    #print(len(nodelist_gpu),'==',n_gpu)
    #print(len(nodelist_mc),'==',n_mc)
    ci_nodelist[k]=[nodelist_gpu, nodelist_mc]

for k in ci_nodelist:
    nodelist_gpu, nodelist_mc = ci_nodelist[k]
    final_nodelist=collect_hostlist(nodelist_gpu+nodelist_mc)
    file_name = 'ci_'+k+'_node_resume.lst'
    f = open(file_name, 'w')
    f.write(final_nodelist)
    f.close()
