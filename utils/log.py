import numpy as np
import os
import platform

import json
import pandas as pd
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

from collections import OrderedDict
from time import time, strftime, localtime

logdata = OrderedDict({})
FMT = '%Y-%m-%d %H:%M:%S'
FILE_FMT = '%Y%m%d_%H%M%S'
FILE_PREFIX =  strftime(FILE_FMT, localtime(time()))


def time_to_str(tm):
  return strftime(FMT, localtime(tm))
  
def LOG(s, mark=False):
  now = time()
  str_now = time_to_str(now)
  idx = "{:04} ".format(len(logdata) + 1)
  logdata[idx + str_now] = str(s)
  msg = '[{}{}] {}'.format(idx,str_now, str(s))
  if mark:
    print('\x1b[1;32m' + msg + '\x1b[0m', flush=True)
  else:
    print(msg, flush=True)
  save_json(logdata, folder='logs')
  return
  

def cwd():
  return os.getcwd()
  
  
def get_packages():
  import pkg_resources
  packs = [x for x in pkg_resources.working_set]
  maxlen = max([len(x.key) for x in packs]) + 1
  packs = [
    "{}{}".format(x.key + ' ' * (maxlen - len(x.key)), x.version) for x in packs
  ]
  packs = sorted(packs)  
  return packs


def save_json(obj, fn='', folder='results'):
  running_in_docker = os.environ.get('AIXP_DOCKER', False)
  subfolder = os.path.join('./output', folder)
  os.makedirs(subfolder, exist_ok=True)
  fn = "{}{}{}.txt".format(
    FILE_PREFIX, 
    "_dokr" if running_in_docker else '_bare',
    ('_' + fn) if len(fn) > 0 else ''
  )  
  path = os.path.join(subfolder, fn)
  with open(path, 'wt') as fh:
    json.dump(obj, fh, indent=4)
  return

def get_empty_train_log():

  dct_result = OrderedDict()
  dct_result['DEVICE']        = None
  dct_result['DATE']          = time_to_str(time())
  dct_result['DOCKER']        = None
  dct_result['OS']            = platform.platform()
  dct_result['OS_SHORT']      = None
  dct_result['TEST_VERSION']  = None
  dct_result['TOTAL_TIME']    = None

  dct_result['NR_BATCHES']    = None
  
  dct_result['EPOCH_TIMINGS'] = []
  dct_result['EPOCH_MIN']     = None
  dct_result['EPOCH_MAX']     = None
  dct_result['EPOCH_STD']     = None
  
  dct_result['BATCH_TIMINGS'] = []
  dct_result['BATCH_MIN']     = None
  dct_result['BATCH_MAX']     = None
  dct_result['BATCH_STD']     = None
  
  dct_result['EVAL_TIMINGS']  = []
  dct_result['EVAL_MIN']      = None
  dct_result['EVAL_MAX']      = None
  dct_result['EVAL_STD']      = None


  dct_result['INFER_TIMINGS']  = []
  dct_result['INFER_MIN']      = None
  dct_result['INFER_MAX']      = None
  dct_result['INFER_STD']      = None
  dct_result['INFER_CNT']      = None
  
  dct_result['INFER_GAIN']     = None
  
  dct_result['BEST_EPOCH']    = 0
  dct_result['BEST_DEV']      = 0
  dct_result['FN']            = None
  dct_result['MODEL']         = None 
  return dct_result

def show_train_log(dct_result, skip=['FN', 'MODEL']):
  maxk = max(len(x) for x in dct_result)
  for k in dct_result:
    if isinstance(dct_result[k], list):
      fv = round(np.mean(dct_result[k]),5)
      v = "{:.4f}s".format(fv)    
      dct_result[k] = fv
    else:
      v = str(dct_result[k])     
      if not isinstance(dct_result[k], (int, float)):
        dct_result[k] = v
    if k in skip:
      continue
    LOG("{} {}".format(
      k + ' ' * (maxk - len(k)), 
      v,
    ))
  return
  

def history_report(folder='./output/results', 
                   history='./data/runs',
                   stats_columns=[
                     'EPOCH_TIMINGS',
                     'EPOCH_STD',
                     'BATCH_TIMINGS', 
                     'BATCH_STD', 
                     'EVAL_TIMINGS', 
                     'INFER_TIMINGS',
                     'EVAL_STD', 
                     'INFER_STD',
                     'INFER_GAIN',
                   ],
                   rename_columns=[
                     'EPOCH_TIME',
                     'EPOCH_STD',
                     'BATCH_TIME', 
                     'BATCH_STD', 
                     'EVAL_TIME', 
                     'INFER_TIME',
                     'EVAL_STD', 
                     'INFER_STD',
                     'INFER_GAIN',
                   ],
                   stats_lines=['count', 'mean', 'min', 'max','std']
                   ):
  files1 = os.listdir(folder)
  files1 = [os.path.join(folder, x) for x in files1 if ('.txt' in x or '.json' in x)]
  files2 = os.listdir(history)
  files2 = [os.path.join(history, x) for x in files2 if ('.txt' in x or '.json' in x)]
  files = files1 + files2
  lst_data = []
  for fn in files:
    try:
      with open(fn, 'rt') as fh:
        data = json.load(fh)
        data['JSON'] = fn
      lst_data.append(data)
    except:
      pass
  devices = set(x['DEVICE'] for x in lst_data)
  for device in devices:
    LOG("**********************************************************")
    LOG("History report for device '{}'".format(device))
    dev_data = [x for x in lst_data if x['DEVICE'] == device]
    dokr_data = [x for x in dev_data if (x.get('DOCKER', False) or 'dokr' in x['JSON'])]
    bare_data = [x for x in dev_data if not (x.get('DOCKER', False) or 'dokr' in x['JSON'])]
    bare_infer_mean = None
    dokr_infer_mean = None
    if len(bare_data) > 0:
      df_bare = pd.DataFrame(bare_data)
      bare_epoch_mean = df_bare['EPOCH_TIMINGS'].mean()
      bare_batch_mean = df_bare['BATCH_TIMINGS'].mean()
      bare_eval_mean = df_bare['EVAL_TIMINGS'].mean()
      if 'INFER_TIMINGS' in df_bare.columns:
        bare_infer_mean = df_bare['INFER_TIMINGS'].mean() 
      df_bare = df_bare[[x for x in stats_columns if x in df_bare.columns]]
      renamer = {k:v for k,v in zip(stats_columns, rename_columns) if k in df_bare.columns}
      df_bare.rename(columns=renamer, inplace=True)
      df_stats = df_bare.describe().loc[stats_lines]
      descr = "\n".join(['        ' + x for x in str(df_stats).split('\n')])
      LOG("  Direct run:\n{}".format(descr))
    if len(dokr_data) > 0:
      df_dokr = pd.DataFrame(dokr_data)
      dokr_epoch_mean = df_dokr['EPOCH_TIMINGS'].mean()
      dokr_batch_mean = df_dokr['BATCH_TIMINGS'].mean()
      dokr_eval_mean = df_dokr['EVAL_TIMINGS'].mean()
      if 'INFER_TIMINGS' in df_dokr.columns:
        dokr_infer_mean = df_dokr['INFER_TIMINGS'].mean() 
      df_dokr = df_dokr[[x for x in stats_columns if x in df_dokr.columns]]
      renamer = {k:v for k,v in zip(stats_columns, rename_columns) if k in df_dokr.columns}
      df_dokr.rename(columns=renamer, inplace=True)
      df_stats = df_dokr.describe().loc[stats_lines]
      descr = "\n".join(['        ' + x for x in str(df_stats).split('\n')])
      LOG("  Docker run:\n{}".format(descr))
    if len(dokr_data) > 0 and len(bare_data) > 0:
      
      LOG("  Bare vs Docker gains for '{}':".format(device))
      LOG("    Epoch: {:>4.1f}%".format((dokr_epoch_mean - bare_epoch_mean) / dokr_epoch_mean * 100))
      LOG("    Batch: {:>4.1f}%".format((dokr_batch_mean - bare_batch_mean) / dokr_batch_mean * 100))
      LOG("    Eval:  {:>4.1f}%".format((dokr_eval_mean - bare_eval_mean) / dokr_eval_mean * 100))
      if dokr_infer_mean is not None and bare_infer_mean is not None:
        LOG("    Infer: {:>4.1f}%".format((dokr_infer_mean - bare_infer_mean) / dokr_infer_mean * 100))        
  return

    