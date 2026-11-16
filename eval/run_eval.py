import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.rag.qa import answer, retrieve

PERGUNTAS_PATH = Path(__file__).parent / "perguntas.json"


def avaliar(k: int) -> dict:
    perguntas = json.loads(PERGUNTAS_PATH.read_text())

    resultados = []
    for item in perguntas:
        start = time.perf_counter()
        hits = retrieve(item["pergunta"], k)
        resposta = answer(item["pergunta"], k)
        tempo = time.perf_counter() - start

        documentos_recuperados = {h["metadata"]["file_name"] for h in hits}
        esperado = item["documento_esperado"]

        if item["respondivel"]:
            recall = esperado in documentos_recuperados if esperado else False
            recusou = "não encontrei" in resposta["resposta"].lower() or "não é possível" in resposta["resposta"].lower()
        else:
            recall = None
            recusou = "não encontrei" in resposta["resposta"].lower()

        resultados.append({
            "pergunta": item["pergunta"],
            "respondivel": item["respondivel"],
            "documento_esperado": esperado,
            "documentos_recuperados": sorted(documentos_recuperados),
            "recall_ok": recall,
            "recusou": recusou,
            "resposta": resposta["resposta"],
            "tempo_segundos": round(tempo, 2),
        })

    respondiveis = [r for r in resultados if r["respondivel"]]
    nao_respondiveis = [r for r in resultados if not r["respondivel"]]

    recall_rate = sum(1 for r in respondiveis if r["recall_ok"]) / len(respondiveis)
    recusa_indevida = sum(1 for r in respondiveis if r["recusou"])
    recusa_correta_rate = sum(1 for r in nao_respondiveis if r["recusou"]) / len(nao_respondiveis)
    tempo_medio = sum(r["tempo_segundos"] for r in resultados) / len(resultados)

    return {
        "k": k,
        "recall_rate": round(recall_rate, 3),
        "recusa_indevida_em_respondiveis": recusa_indevida,
        "recusa_correta_rate_em_nao_respondiveis": round(recusa_correta_rate, 3),
        "tempo_medio_segundos": round(tempo_medio, 2),
        "detalhes": resultados,
    }


if __name__ == "__main__":
    for k in (3, 5):
        print(f"\n=== Avaliação com k={k} ===")
        resumo = avaliar(k)
        print(f"Recall (trecho certo no top-k): {resumo['recall_rate'] * 100:.1f}%")
        print(f"Recusas indevidas (deveria responder, recusou): {resumo['recusa_indevida_em_respondiveis']}")
        print(f"Recusa correta em perguntas fora do domínio: {resumo['recusa_correta_rate_em_nao_respondiveis'] * 100:.1f}%")
        print(f"Tempo médio por pergunta: {resumo['tempo_medio_segundos']}s")

        out_path = Path(__file__).parent / f"resultado_k{k}.json"
        out_path.write_text(json.dumps(resumo, ensure_ascii=False, indent=2))
        print(f"Detalhes salvos em {out_path}")
