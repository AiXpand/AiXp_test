# -*- coding: utf-8 -*-
"""
Copyright 2017-2022 Lummetry.AI (Knowledge Investment Group SRL). All Rights Reserved.


* NOTICE:  
*   All information contained herein is, and remains the property of Knowledge Investment Group SRL.  
*   The intellectual and technical concepts contained herein are proprietary to Knowledge Investment Group SRL
*   and may be covered by Romanian and Foreign Patents, patents in process, and are protected by trade secret 
*   or copyright law. Dissemination of this information or reproduction of this material * is strictly forbidden 
*   unless prior written permission is obtained from Knowledge Investment Group SRL.



@copyright: Lummetry.AI
@author: Lummetry.AI - AID
@project: 
@description:
Created on Sat Feb 25 13:44:23 2023
"""
import torch as th
from copy import deepcopy
from time import time
from collections import OrderedDict

from models.simple_classifiers import AbstractClassifier

def train_classifier(model : AbstractClassifier, 
                     train_loader, test_loader,
                     optimizer=th.optim.NAdam, lr=1e-4,
                     loss=th.nn.CrossEntropyLoss(), epochs=100,
                     earlystopping=True, patience=5,
                     log_func=print, progress_delta=4e-4
                     ):
  log_func("Starting training of '{}'".format(model.__class__.__name__))
  dct_result = OrderedDict()
  dct_result['EPOCH_TIMINGS'] = []
  dct_result['BATCH_TIMINGS'] = []
  dct_result['EVAL_TIMINGS']  = []
  dct_result['BEST_EPOCH']    = 0
  dct_result['BEST_DEV']      = 0
  dct_result['FN']            = None
  dct_result['MODEL']         = None
  optim = optimizer(params=model.parameters(), lr=lr)
  lost_patience = 0
  for epoch in range(1, epochs + 1):
    t0epoch = time()
    log_func("  Starting epoch {:03}".format(epoch))   
    for th_bx, th_by in train_loader:
      t0batch = time()
      th_yh = model(th_bx)
      th_loss = loss(input=th_yh, target=th_by)
      optim.zero_grad()
      th_loss.backward()
      optim.step()
      dct_result['BATCH_TIMINGS'].append(time() - t0batch)
    # end epoch
    dct_result['EPOCH_TIMINGS'].append(time() - t0epoch)
    
    t0dev = time()
    dev_result = model.evaluate(test_loader)
    dct_result['EVAL_TIMINGS'].append(time() - t0dev)
    
    if (dct_result['BEST_DEV'] + progress_delta) < dev_result:
      dct_result['BEST_DEV'] = dev_result
      dct_result['BEST_EPOCH'] = epoch
      best_weights = deepcopy(model.state_dict())
      lost_patience = 0
      log_func("    Found new best acc={:.2f}% at epoch {}".format(dev_result * 100, epoch))
    else:
      lost_patience += 1
      
    if lost_patience > patience:
      model.load_state_dict(best_weights)
      dct_result['MODEL'] = model
      break
  # end epochs
  fn = model.save_to_file()
  dct_result['FN'] = fn
  return dct_result
    
  