
import math
import streamlit as st

st.set_page_config(
    page_title="Calculadora Enem 2026 | 1º dia",
    page_icon="📝",
    layout="wide"
)

# Referencias preliminares de 2012 a 2025.
# Ainda nao auditadas nos arquivos originais do Inep.
# NAO sao parametros psicometricos a, b e c.

REFERENCIAS = {
    "Linguagens": {
        "notas": (500, 600, 650, 700),
        "acertos": [
            (16, 30, 37, 41),
            (18, 32, 37, 41),
            (18, 30, 35, 39),
            (18, 28, 33, 38),
            (16, 26, 31, 36),
            (16, 26, 31, 36),
            (14, 29, 36, 39),
            (13, 24, 30, 35),
            (16, 29, 36, 40),
            (12, 22, 29, 34),
            (17, 28, 34, 38),
            (16, 28, 34, 39),
            (18, 30, 35, 39),
            (18, 30, 35, 39),
        ],
    },
    "Ciências Humanas": {
        "notas": (500, 600, 650, 700, 750),
        "acertos": [
            (14, 24, 31, 36, 40),
            (16, 28, 34, 38, 41),
            (18, 30, 35, 39, 42),
            (15, 25, 31, 36, 40),
            (14, 24, 31, 36, 40),
            (14, 22, 29, 35, 40),
            (14, 25, 31, 36, 40),
            (10, 16, 24, 33, 39),
            (13, 22, 28, 33, 37),
            (14, 23, 28, 34, 38),
            (13, 22, 29, 36, 40),
            (14, 23, 29, 35, 39),
            (15, 22, 27, 32, 36),
            (16, 25, 30, 34, 38),
        ],
    },
}


def interpolar(x, xs, ys):
    for i in range(1, len(xs)):
        if x <= xs[i]:
            t = (
                (x - xs[i - 1])
                / (xs[i] - xs[i - 1])
            )
            return (
                ys[i - 1]
                + t * (ys[i] - ys[i - 1])
            )

    t = (
        (x - xs[-2])
        / (xs[-1] - xs[-2])
    )

    return ys[-2] + t * (ys[-1] - ys[-2])


def prever(n_acertos, area):

    tabela = REFERENCIAS[area]
    notas_ref = tabela["notas"]

    medias = [
        sum(
            linha[j]
            for linha in tabela["acertos"]
        ) / len(tabela["acertos"])
        for j in range(len(notas_ref))
    ]

    # Pontos extremos assumidos pelo modelo.
    xs = (300,) + notas_ref + (850,)
    ys = (0.5,) + tuple(medias) + (44.5,)

    notas = list(range(300, 851))
    logpesos = []

    # Modelo exploratorio de Poisson.
    for nota in notas:

        taxa = max(
            0.05,
            min(
                44.9,
                interpolar(nota, xs, ys)
            )
        )

        logp = (
            n_acertos * math.log(taxa)
            - taxa
            - math.lgamma(n_acertos + 1)
        )

        logpesos.append(logp)

    maior = max(logpesos)

    pesos = [
        math.exp(p - maior)
        for p in logpesos
    ]

    total = sum(pesos)

    probs = [
        p / total
        for p in pesos
    ]

    estimativa = sum(
        nota * p
        for nota, p in zip(notas, probs)
    )

    acumulado = 0.0
    inferior = None
    superior = None

    for nota, p in zip(notas, probs):

        acumulado += p

        if inferior is None and acumulado >= 0.10:
            inferior = nota

        if superior is None and acumulado >= 0.90:
            superior = nota
            break

    return round(estimativa), inferior, superior


# =========================================
# INTERFACE DA CALCULADORA
# =========================================

st.title("Calculadora de notas do Enem 2026")

st.caption(
    "Primeiro dia | Linguagens e Ciências Humanas"
)

st.warning(
    "Esta calculadora apresenta uma simulação "
    "estatística experimental, não a nota oficial "
    "do Inep nem uma calibração TRI 3PL. "
    "As referências históricas de 2012 a 2025 "
    "ainda precisam ser auditadas e os dados de "
    "2009 a 2011 não foram incorporados."
)

col_cor, col_idioma = st.columns(2)

with col_cor:
    cor = st.selectbox(
        "Cor do caderno",
        [
            "Azul (1)",
            "Amarelo (2)",
            "Branco (3)"
        ]
    )

with col_idioma:
    idioma = st.selectbox(
        "Língua estrangeira",
        ["Inglês", "Espanhol"]
    )

st.write(
    "**Marque somente as questões que acertou**, "
    "conforme a numeração do seu caderno."
)

with st.form("respostas"):

    totais = {}

    for area, inicio in (
        ("Linguagens", 1),
        ("Ciências Humanas", 46)
    ):

        st.subheader(area)

        marcadas = []

        for linha in range(5):

            colunas = st.columns(9)

            for coluna in range(9):

                numero = (
                    inicio + 9 * linha + coluna
                )

                with colunas[coluna]:

                    marcado = st.checkbox(
                        str(numero),
                        key=f"{cor}:{idioma}:{numero}"
                    )

                    if marcado:
                        marcadas.append(numero)

        totais[area] = len(marcadas)

    conferiu = st.checkbox(
        "Conferi todas as 90 questões; "
        "as não marcadas não foram acertadas.",
        value=False
    )

    calcular = st.form_submit_button(
        "Calcular possíveis notas",
        type="primary",
        use_container_width=True
    )


# =========================================
# RESULTADOS
# =========================================

if calcular:

    if not conferiu:

        st.error(
            "Confirme a conferência das "
            "90 questões para calcular."
        )

    else:

        st.divider()

        st.subheader("Resultado preliminar")

        col1, col2 = st.columns(2)

        for coluna, area in (
            (col1, "Linguagens"),
            (col2, "Ciências Humanas")
        ):

            nota, menor, maior = prever(
                totais[area],
                area
            )

            with coluna:

                st.metric(
                    area,
                    f"{nota} pontos"
                )

                st.write(
                    f"**Acertos:** "
                    f"{totais[area]}/45"
                )

                st.write(
                    f"**Faixa indicativa:** "
                    f"{menor} a {maior} pontos"
                )

        st.caption(
            "As faixas são indicativas do modelo "
            "exploratório, não intervalos de "
            "confiança validados. "
            "O cálculo utiliza a quantidade de "
            "acertos e não estima os parâmetros "
            "psicométricos das questões individuais."
        )
