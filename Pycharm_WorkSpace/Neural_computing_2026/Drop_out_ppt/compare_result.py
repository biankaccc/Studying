# compare_result.py
import torch
import matplotlib.pyplot as plt
import numpy as np

def plot_compare():
    h_no = torch.load("history_no_dropout.pt", weights_only=False)
    h_drop = torch.load("history_with_dropout.pt", weights_only=False)

    train_no = h_no["train_loss"]
    val_no = h_no["val_loss"]
    train_drop = h_drop["train_loss"]
    val_drop = h_drop["val_loss"]

    epochs = np.arange(len(train_no))
    plt.figure(figsize=(10,6))
    plt.plot(epochs, train_no, 'r-', label='Train (No Dropout)')
    plt.plot(epochs, val_no, 'r--', label='Val (No Dropout)')
    plt.plot(epochs, train_drop, 'b-', label='Train (With Dropout)')
    plt.plot(epochs, val_drop, 'b--', label='Val (With Dropout)')
    plt.title("Dropout vs No Dropout - Bike Sharing Regression")
    plt.xlabel("Epoch")
    plt.ylabel("MSE Loss")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.show()

    print("=== Summary ===")
    print(f"No Dropout: min val loss = {min(val_no):.6f}, epoch {np.argmin(val_no)}")
    print(f"With Dropout: min val loss = {min(val_drop):.6f}, epoch {np.argmin(val_drop)}")

if __name__ == "__main__":
    plot_compare()
