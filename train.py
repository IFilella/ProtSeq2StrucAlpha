import json
import torch
from torch.utils.data import DataLoader, Dataset, random_split
import torch.optim as optim
import random
import glob
import wandb
from utils.timer import Timer
from utils.foldseek import get_struc_seq
from tokenizer import SequenceTokenizer, FoldSeekTokenizer

"""
def masking_seq(seq, mask_token, mask_ratio=0.15):
    seq = list(seq)
    seq = [seq[i] + seq[i+1] for i in range(0, len(seq), 2)]
    num_to_mask = int(len(seq) * mask_ratio)
    # randomly select indices from the sequence
    mask_indices = random.sample(range(int(len(seq)/2)), num_to_mask)
    mask_indices = [(i*2)+1 for i in mask_indices]
    for i in mask_indices:
        seq[i] = seq[i][0] + mask_token
    return seq

masking_seq(seq='AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRr', mask_token='#')
"""

class SeqsDataset(Dataset):
    def __init__(self, aa_seqs, struc_seqs,
                 tokenizer_aa_seqs, tokenizer_struc_seqs,
                 max_len=1024):
        self.aa_seqs = aa_seqs
        self.struc_seqs = struc_seqs
        self.tokenizer_aa_seqs = tokenizer_aa_seqs
        self.tokenizer_struc_seqs = tokenizer_struc_seqs
        self.max_len = max_len

    def __len__(self):
        return len(self.aa_seqs)

    def __getitem__(self, idx):
        # Tokenize protein sequence of index idx
        aa_seq = self.aa_seqs[idx]
        encoded_aa_seq = self.tokenizer_aa_seqs(aa_seq,
                                                truncation=True,
                                                padding=True,
                                                max_len=self.max_len)

        # Tokenize structural sequence of index idx
        struc_seq = self.struc_seqs[idx]
        encoded_struc_seq = self.tokenizer_struc_seqs(struc_seq,
                                                      truncation=True,
                                                      padding=True,
                                                      max_len=self.max_len)
        return {
            'encoder_input_ids': encoded_aa_seq['input_ids'].squeeze(),
            'encoder_attention_mask': encoded_aa_seq['attention_mask'].squeeze(),
            'decoder_input_ids': encoded_struc_seq['input_ids'].squeeze(),
            'decoder_attention_mask': encoded_struc_seq['attention_mask'].squeeze()
        }

        
def evaluate_model(model,
                   test_loader,
                   criterion,
                   device='cuda',
                   verbose=False):
    """
    Evaluate the model on the test dataset with gradient calculation.

    Args:
        model (torch.nn.Module): The trained model.
        test_loader (DataLoader): DataLoader for the test dataset.
        criterion: The loss function.
        device (str): Device to run the evaluation on ('cuda' or 'cpu').
        verbose (bool): Whether to print progress.

    Returns:
        dict: A dictionary containing 'avg_loss' and 'accuracy'.
    """
    model.train()  # Ensure the model is in training mode for gradient calculations
    total_loss = 0.0
    total_correct = 0
    total_samples = 0

    for batch in test_loader:
        
        input_ids = batch['encoder_input_ids'].to(device)
        attention_mask = batch['encoder_attention_mask'].to(device)
        decoder_input_ids = batch['decoder_input_ids'].to(device)
        decoder_attention_mask = batch['decoder_attention_mask'].to(device)

        # Forward pass
        outputs = model(input_ids=input_ids,
                        attention_mask=attention_mask,
                        decoder_input_ids=decoder_input_ids,
                        decoder_attention_mask=decoder_attention_mask)
        
        # Compute loss
        loss = criterion(outputs.logits, decoder_input_ids)
        total_loss += loss.item()

        # Compute accuracy (for classification tasks)
        _, predicted = torch.max(outputs.logits, dim=-1)
        total_correct += (predicted == decoder_input_ids).sum().item()
        total_samples += decoder_input_ids.numel()

        if verbose:
            print(f"Processed batch with loss: {loss.item():.4f}")

    # Average loss and accuracy over the entire test set
    avg_loss = total_loss / len(test_loader)
    accuracy = total_correct / total_samples

    if verbose:
        print(f"Test Loss: {avg_loss:.4f}, Test Accuracy: {accuracy:.4f}")

    return {"avg_loss": avg_loss, "accuracy": accuracy}


def train_model(model,
                train_loader,
                optimizer,
                criterion,
                epochs,
                device='cuda',
                verbose=False):
    """
    Train the model using the specified hyperparamaters

    Args:
        model (model class ...): ....
        train_loader (DataLoader): ...
        optimizer (...): ...
        criterion (...): ...
        epochs (int): Number of epochs
        device (...): ...
        verbose (bool): ...
    """    
    pass


def main(confile):
    
    with open(confile, 'r') as f:
        config = json.load(f)

    # Get the data
    structures_dir = config["data_path"]
    pdbs = glob.glob('%s*.pdb' % structures_dir)

    # Get protein sequence and structural sequence (FoldSeeq) from raw data
    foldseek_path = config["foldseek_path"]
    raw_data = [get_struc_seq(foldseek_path, pdb, chains=['A'])['A'] for pdb in pdbs]
    aa_seqs = [pdb[0] for pdb in raw_data]
    struc_seqs = [pdb[1] for pdb in raw_data]

    # Load Dataset
    tokenizer_aa_seqs = SequenceTokenizer()
    tokenizer_struc_seqs = FoldSeekTokenizer()
    dataset = SeqsDataset(aa_seqs, struc_seqs,
                          tokenizer_aa_seqs, tokenizer_struc_seqs,
                          max_len=1024)

    # Split Dataset into training and testing
    test_split = config["test_split"]
    test_size = int(test_split * len(dataset))
    train_size = len(dataset) - test_size
    train_dataset, test_dataset = random_split(dataset, [train_size, test_size])

    # Load DataLoader
    batch_size = config['batch_size']
    train_loader =  DataLoader(train_dataset, batch_size=batch_size, shuffle=True) 
    test_loader =  DataLoader(test_dataset, batch_size=batch_size, shuffle=True)

    # Get model hyperparamaters
    epochs = config['epochs']
    learning_rate = config['learning_rate']
    
    # Initialize model, optimizer, and loss function
    #model = 
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    criterion = 
    
    timer = Timer(autoreset=True)
    timer.start('Training started')
    for epoch in range(epochs):
        print(f"Epoch {epoch+1}/{epochs}")
    
        # Train the model
        train_model(model,
                    train_loader,
                    optimizer,
                    criterion,
                    device='cuda',
                    verbose=False)
        
        # Evaluate the model
        evaluation_results = evaluate_model(model,
                                            test_loader,
                                            criterion,
                                            device='cuda',
                                            verbose=False)
        
        print(f"Evaluation Results - Loss: {evaluation_results['avg_loss']}, Accuracy: {evaluation_results['accuracy']}")
        
        # Log the evaluation results to wandb if applicable
        get_wandb = config['get_wandb']
        if get_wandb:
            wandb.init(project=config["wandb_project"],
                       config={"dataset": "sample_DB",
                               "architecture": "Transformer"})
            wandb.log({"epoch": epoch + 1, 
                       "loss": evaluation_results['avg_loss'], 
                       "accuracy": evaluation_results['accuracy']})
    
    timer.stop('Training ended')


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--config', type=str, default='config.json', help='Configuration file')
    args = parser.parse_args()

    confile = args.config

    main(confile=confile)
