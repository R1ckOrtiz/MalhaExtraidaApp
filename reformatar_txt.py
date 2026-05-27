import csv

# Cabeçalhos baseados no Excel (38 colunas)
headers = [
    'M', 'Lat', 'Long', 'altura', 'raio', 'direção', 'pto_notaveis',
    'KM_esq', 'vel_esq_s', 'vel_esq_d', 'KM_pri', 'vel_pri_s', 'vel_pri_d',
    'KM_dir', 'vel_dir_s', 'vel_dir_d', 'Nome_SB', 'Nome_SB_dir', 'Nome_SB_esq',
    'Estado', 'Vel1_cre', 'Vel1_decre', 'Vel2_cre', 'Vel2_decre', 'Vel3_decre',
    'Vel3_cre', 'Vel4_decre', 'Vel4_cre', 'Vel5_decre', 'Vel5_cre', 'Vel6_decre',
    'Vel6_cre', 'Vel7_decre', 'Vel7_cre', 'Estado_via', 'Acao_via', 'Tempo_sub', 'Tempo_desc'
]

def reformat_txt_to_csv(arquivo_txt, arquivo_csv):
    with open(arquivo_txt, 'r', encoding='utf-8') as f_in, \
         open(arquivo_csv, 'w', newline='', encoding='utf-8') as f_out:
        writer = csv.writer(f_out, delimiter=';')  # Usando ; como delimitador para compatibilidade
        writer.writerow(headers)
        for linha in f_in:
            campos = linha.strip().split()
            if len(campos) == 38:  # Verificar se tem 38 campos
                writer.writerow(campos)

if __name__ == "__main__":
    arquivo_txt = "Malha__exportado.txt"
    arquivo_csv = "Malha_formatada.csv"
    reformat_txt_to_csv(arquivo_txt, arquivo_csv)
    print(f"Arquivo CSV gerado: {arquivo_csv}")