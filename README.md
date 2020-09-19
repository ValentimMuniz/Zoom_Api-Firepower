# Zoom Web Service API para o Firepower Objects Parser

Este é um script de amostra que analisa IP's e URL's publicados no site da <a href = "https://support.zoom.us/hc/en-us/articles/201362683-Network-firewall-or-proxy-server-settings-for-Zoom">Zoom</a>. O script analisará todos os IP's e URL's de serviço de Web do Zoom em 2 lista (respectivamente) e usará a API do FMC para carregar em 2 objetos de grupo. Esses objetos de grupo podem ser usados ​​em uma regra de "trust" / "prefilter" do FirePower. Ao fazer isso, o tráfego é excluído de inspeção adicional para evitar problemas de latência com os aplicativos Zoom.

# Features
• Pegar todos IPs e URLs  do Zoom com REST-based web service;
• Criação do formato JSON correto para API do FMC (PUT requests)
• Upa este JSON para o FMC, sobrescrevendo o Objeto de Grupo anterior;
• Checa se o arquivo do Zoom foi atualizado e aplica a atualização automáticamente;
• Auto-Deploy de política usando API quando mudanças foram feitas nos Objetos (OPCIONAL*** E cuidado, isso também implementará outras mudanças de política não relacionadas);
• Alerta via Webex Teams quando alguma mudança no objeto for feita;
• Verificação constante se há atualizações com um intervalo de tempo especificado (OPCIONAL).

# Cisco Products / Services
• Cisco Firepower Management Center;
• Cisco Firepower Threat Defense NGFW.

# Instalação
Essas instruções permitirão que você baixe o script e execute-o, de modo que a saída possa ser usada no Firepower como Group Objects. O que você precisa para começar? Lista de tarefas abaixo:
