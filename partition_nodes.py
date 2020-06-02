from hostlist import expand_hostlist, collect_hostlist
import random

# from partition "normal"
mc_nodes="your list here"

gpu_nodes="your list here"


exp_mc = expand_hostlist(mc_nodes)
exp_gpu = expand_hostlist(gpu_nodes)
total_mc = len(exp_mc)
total_gpu = len(exp_gpu)


print("# MC nodes: %d" % (total_mc))
print("# GPU nodes: %d" % (total_gpu))

ci=[ 'CI',  'PT_em', 'PT_eth', 'PT_mr', 'PT_u', 'PA_pr', 'PA_ul', 'PA_rest', 'CE_ich', 'CE_uzh' ]
ci_mc=[  1/9, 1/9, 1/9, 1/9, 1/9, 0.0, 1/9, 1/9, 1/9, 1/9 ]
ci_gpu=[ 1/5, 0.0, 1/5, 0.0, 0.0, 1/5, 1/5, 1/5, 0.0, 0.0 ]

ci_nnodes=dict()
rest_mc=0.0
rest_gpu=0.0
for idx, c in enumerate(ci):
    n_gpu = int(ci_gpu[idx]*total_gpu)
    rest_gpu+=ci_gpu[idx]*total_gpu-n_gpu
    n_mc = int(ci_mc[idx]*total_mc)
    rest_mc+= ci_mc[idx]*total_mc-n_mc
    ci_nnodes[c]=[ n_gpu, n_mc ]

rest_gpu = int(rest_gpu)
rest_mc = int(rest_mc)
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
