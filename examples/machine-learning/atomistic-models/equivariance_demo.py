"""用 e3nn 核对等变张量积；用法：python equivariance_demo.py。"""
import json
from pathlib import Path

import torch
with torch.serialization.safe_globals([slice]):
    from e3nn import o3


def main():
    torch.set_default_dtype(torch.float64)
    torch.manual_seed(7)
    incoming = o3.Irreps("2x0e + 1x1o")
    edge = o3.Irreps("1x1o")
    outgoing = o3.Irreps("2x0e + 1x1o + 1x2e")
    tensor_product = o3.FullyConnectedTensorProduct(incoming, edge, outgoing)
    x = incoming.randn(4, -1)
    direction = edge.randn(4, -1)
    rotation = o3.rand_matrix()
    y = tensor_product(x, direction)
    rotated_y = tensor_product(x @ incoming.D_from_matrix(rotation).T,
                               direction @ edge.D_from_matrix(rotation).T)
    expected = y @ outgoing.D_from_matrix(rotation).T
    error = float((rotated_y - expected).abs().max().detach())
    assert error < 1e-8
    scalar_vector_only = o3.FullyConnectedTensorProduct("1x1o", "1x1o", "1x0e")
    u, v = torch.tensor([[1., 2., 0.]]), torch.tensor([[3., -1., 0.]])
    scalar_vector_only.weight.data.fill_(1.0)
    assert torch.allclose(scalar_vector_only(u, v), scalar_vector_only(u @ rotation.T, v @ rotation.T), atol=1e-8)
    report = {"input_dimension": incoming.dim, "edge_dimension": edge.dim,
              "output_dimension": outgoing.dim, "learned_weights": tensor_product.weight_numel,
              "rotation_error": error}
    Path("results").mkdir(exist_ok=True)
    Path("results/equivariance.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
