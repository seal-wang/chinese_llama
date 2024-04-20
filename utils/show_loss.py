#!/usr/bin/env python3

import os
import sys
import json
import matplotlib
from matplotlib import pyplot as plt


def show_loss(file="./output/trainer_state.json"):
    file = os.path.join(file, "trainer_state.json") if os.path.isdir(file) else file
    with open(file, mode='r', encoding='utf-8') as f:
        obj = json.load(f)

    loss_list = [v["loss"] for v in obj["log_history"] if "loss" in v]        
    step_list = [v for v in range(len(loss_list))]

    matplotlib.use("TkAgg")
    plt.plot(step_list, loss_list)
    plt.xlabel("step")
    plt.ylabel("loss")
    plt.show()

if __name__ == "__main__":
    show_loss(sys.argv[1] if len(sys.argv) >= 2 else './')