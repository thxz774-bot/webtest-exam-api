from pathlib import Path

from excel_reader import ler_alunos
from distribuidor import distribuir
from excel_writer import gerar_excel

BASE = Path(__file__).resolve().parent.parent

ALUNOS = BASE / "data" / "alunos.xlsx"
TEMPLATE = BASE / "data" / "template.xlsx"
MAPEAMENTO_GABARITO = BASE / "data" / "mapeamento_gabarito_identificadores.json"
OUTPUT = BASE / "output" / "resultado.xlsx"


def main():

    alunos = ler_alunos(ALUNOS)

    print(f"{len(alunos)} alunos carregados")

    distribuicao = distribuir(alunos)

    print("\nResumo das salas:")

    for sala, dados in distribuicao.items():

        qtd_1 = len(dados["1"])
        qtd_2 = len(dados["2"])
        qtd_3 = len(dados["3"])

        total = qtd_1 + qtd_2 + qtd_3

        print(
            f"Sala {sala}: "
            f"{qtd_1} do 1º ano | "
            f"{qtd_2} do 2º ano | "
            f"{qtd_3} do 3º ano | "
            f"Total: {total}"
        )

    gerar_excel(
        TEMPLATE,
        OUTPUT,
        distribuicao,
        str(MAPEAMENTO_GABARITO)
    )

    print(f"\nArquivo gerado: {OUTPUT}")


if __name__ == "__main__":
    main()
