from autoencoder.models.vanilla_model import AutoEncoder
from torch.utils.data import DataLoader
from tqdm import tqdm
from torch import nn
import torch
import utils
from pathlib import Path
import dvclive
import yaml
import click
from autoencoder.encoders import DenseEncoder, ConvEncoder
from autoencoder.decoders import DenseDecoder, ConvDecoder


device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
# TODO why does 0 go to gpu1, how does torch order gpus?
#device = 'cuda' if torch.cuda.is_available() else 'cpu'

def train_ae(
    log_dir: str,
    epochs: int,
    trainloader: DataLoader,
    ae: torch.nn.Module,
    lr=0.0001,
):
    log_dir = Path(log_dir)
    gen_dir = log_dir/'gen'
    dvclive_dir = log_dir/'logs'
    gen_dir.mkdir(exist_ok=True, parents=True)

    dvclive.init(str(dvclive_dir), summary=True)

    assert len(trainloader) > 0

    ae = ae.to(device)

    # Reference random tensor
    # TODO repeat in shape
    random_tensors = torch.stack([
        # NOTE by doing two of each, two are used at once for VAE
        torch.rand(ae.latent_size), # fix values
        torch.rand(ae.latent_size), # fix values
        torch.randn(ae.latent_size), # fix values
        torch.randn(ae.latent_size), # fix values
    ]).to(device)

    optimizer = torch.optim.Adam(ae.parameters(), lr=lr)

    for epoch in range(epochs):
        print(f"{epoch}/{epochs}")
        running_loss = 0
        total = 0 # use total as drop_last=True
        ae.train()
        for image_b in tqdm(trainloader):
            #print(data[0])
            image_b = image_b.to(device)
            y_pred = ae(image_b)

            loss = ae.criterion(y_pred, image_b)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            running_loss += loss.item()
            total += image_b.size(0)

        print(f"loss: {running_loss/total}")
        dvclive.log("loss", running_loss/total, epoch)
        ae.eval()
        with torch.no_grad():
            #for idx in [0, len(trainloader)//4, len(trainloader)//2]:
                #im.save(str(log_dir/'val'/epoch/f"{idx}.jpg"))
                # TODO don't loop, just do all
                #im = transforms.ToPILImage()(ae(train[idx].to(device))[0].cpu().data)
                #im.save(str(log_dir/'val'/epoch/f"gen_{idx}.jpg"))
            
            generations = ae.predict(random_tensors)
            utils.save(
                generations.cpu(),
                str(gen_dir),
                epoch)
        dvclive.next_step()
    utils.make_gifs(str(gen_dir))

@click.command()
@click.option("--encoder-type", type=click.STRING)
@click.option("--decoder-type", type=click.STRING)
@click.option("--ae-type", type=click.STRING)
@click.option("--latent-size", type=click.INT)
def main(
    encoder_type,
    decoder_type,
    ae_type,
    latent_size,
    lr,
    ):
    encoder_const = DenseEncoder if encoder_type == 'dense' else ConvEncoder
    decoder_const = DenseDecoder if decoder_type == 'dense' else ConvDecoder

    model_const = VAE if ae_type == 'vae' else AutoEncoder

    #ae = model_const()
    pass


if __name__ == "__main__":
    main()