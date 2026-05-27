import re

def extrair_sbs(arquivo):
    sbs = {}
    with open(arquivo, 'r', encoding='utf-8') as f:
        for linha in f:
            campos = linha.strip().split()
            if len(campos) < 20:
                continue
            # Procurar por campos que parecem SBs (ex: LID___P, LIDLAX_)
            for campo in campos:
                if re.match(r'^[A-Z]{3,6}_*_[A-Z]$', campo) or re.match(r'^[A-Z]{6,7}_$', campo):
                    sb = campo
                    if sb not in sbs:
                        sbs[sb] = []
                    # Adicionar a linha completa
                    sbs[sb].append(linha.strip())
    return sbs

if __name__ == "__main__":
    arquivo = "Malha__exportado.txt"
    sbs_extraidos = extrair_sbs(arquivo)
    with open("sbs_extraidos.txt", 'w', encoding='utf-8') as f_out:
        for sb, linhas in sbs_extraidos.items():
            f_out.write(f"SB: {sb}\n")
            f_out.write(f"Número de ocorrências: {len(linhas)}\n")
            for linha in linhas:
                f_out.write(f"{linha}\n")
            f_out.write("\n")