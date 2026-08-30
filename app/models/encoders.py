# module level, loaded once:
#   tokenizer = load tokenizer for EMBEDDING_MODEL_NAME
#   model = load model for EMBEDDING_MODEL_NAME, move to DEVICE, set eval mode

#   def embed(texts: list[str]) -> list[list[float]]:
#       tokenize texts -> input_ids, attention_mask  (batch, pad, truncate)
#       move tensors to DEVICE

#       with no_grad:
#           outputs = model(input_ids, attention_mask)
#           token_embeddings = outputs.last_hidden_state   # (batch, seq_len, 384)

#       pooled = mean_pool(token_embeddings, attention_mask)  # (batch, 384)
#       normalized = l2_normalize(pooled)                     # (batch, 384)

#       return normalized as plain python lists

#4 step gaol 

import torch


from transformers import AutoTokenizer, AutoModel
from app.config import EMBEDDING_MODEL_NAME, DEVICE

tokenizer = AutoTokenizer.from_pretrained(EMBEDDING_MODEL_NAME)
model = AutoModel.from_pretrained(EMBEDDING_MODEL_NAME)
model.to(DEVICE)
model.eval()

def mean_pool(token_embeddings: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
    """Mean Pooling - Take attention mask into account for correct averaging."""
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
    sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
    return sum_embeddings / sum_mask

def l2_normalize(embeddings: torch.Tensor) -> torch.Tensor:
    """L2 normalize embeddings."""
    return torch.nn.functional.normalize(embeddings, p=2, dim=1)


def embed(texts: list[str]) -> list[list[float]]:
    inputs = tokenizer(
        texts,
        return_tensors="pt",
        padding=True,
        truncation=True,
    )
    inputs = {k: v.to(DEVICE) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)
        token_embeddings = outputs.last_hidden_state  # (batch, seq_len, 384)

    attention_mask = inputs["attention_mask"]
    pooled = mean_pool(token_embeddings, attention_mask)  # (batch, 384)
    normalized = l2_normalize(pooled)                      # (batch, 384)

    return normalized.cpu().tolist()


