"""Anomaly detection demonstration using only synthetic security telemetry.
No automatic blocking, no external model/LLM and no secret-bearing feature.
"""
from __future__ import annotations
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

FEATURES = ('failed_logins_5m', 'tls_errors_5m', 'cross_site_denials_5m', 'sqli_attempts_5m', 'events_per_minute')


def make_fixture(seed=712, train_count=600, test_benign=160, test_attack=80):
    """Independent synthetic train/test, labels are scenario ground truth."""
    rng=np.random.default_rng(seed)
    def benign(n):
        return np.column_stack((rng.poisson(.45,n),rng.poisson(.08,n),rng.poisson(.04,n),rng.poisson(.02,n),rng.normal(12,2.5,n).clip(0))).astype(float)
    train=benign(train_count)
    normal=benign(test_benign)
    attacks=benign(test_attack)
    groups=np.arange(test_attack)%4
    attacks[groups==0,0]+=rng.integers(7,15,(groups==0).sum())
    attacks[groups==1,1]+=rng.integers(5,12,(groups==1).sum())
    attacks[groups==2,2]+=rng.integers(5,10,(groups==2).sum())
    attacks[groups==3,3]+=rng.integers(4,10,(groups==3).sum())
    x=np.vstack((normal,attacks))
    y=np.array([0]*test_benign+[1]*test_attack,dtype=int)
    # Deterministic shuffled holdout, not training data.
    ix=rng.permutation(len(y))
    return train,x[ix],y[ix]


def evaluate(seed=712):
    train,test,y=make_fixture(seed)
    model=IsolationForest(n_estimators=150,contamination=.08,random_state=seed,n_jobs=1)
    model.fit(train)
    # 8th-percentile train score: fixed threshold calibrated on BENIGN TRAINING SET ONLY.
    threshold=float(np.percentile(model.score_samples(train),8))
    scores=model.score_samples(test)
    pred=(scores<threshold).astype(int)
    tn,fp,fn,tp=map(int,confusion_matrix(y,pred,labels=[0,1]).ravel())
    report={
        'method':'IsolationForest', 'data':'100% SYNTHETIC HOLDOUT', 'random_seed':seed,
        'features':list(FEATURES), 'train_benign':len(train),'test_benign':int((y==0).sum()),
        'test_attack':int((y==1).sum()), 'threshold_train_percentile':8,
        'confusion_matrix':{'TN':tn,'FP':fp,'FN':fn,'TP':tp},
        'accuracy':round(float(accuracy_score(y,pred)),4),
        'precision':round(float(precision_score(y,pred,zero_division=0)),4),
        'recall':round(float(recall_score(y,pred,zero_division=0)),4),
        'f1':round(float(f1_score(y,pred,zero_division=0)),4),
        'alerts_suggested':int(pred.sum()), 'actions_executed':0,
        'human_approval_required':True,
        'privacy':'No payloads, passwords, IP addresses, TOTP seeds, or personal data used as ML features.',
        'limitations':'Synthetic, easily separable attacks; not a field accuracy estimate. False positives and false negatives possible.'
    }
    return report


def triage(report):
    return {'decision':'REVIEW_REQUIRED','severity':'medium',
            'suggested_action':'Solicitar revisao de operador dos alertas antes de isolar dispositivos ou alterar rede',
            'approved':False,'executed':False,'automatic_network_changes':0,
            'alerts_suggested':report['alerts_suggested']}
