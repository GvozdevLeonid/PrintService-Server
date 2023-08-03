// Модальное окно навигации
function open_nav() {
    document.getElementById('nav-modal').classList.remove('invisible');
    document.getElementById('nav-modal-bg').classList.remove('opacity-0');
    document.getElementById('nav-modal-links').classList.add('translate-x-64');

}

function close_nav() {
    document.getElementById('nav-modal-bg').classList.add('opacity-0');
    document.getElementById('nav-modal').classList.add('invisible');
    document.getElementById('nav-modal-links').classList.remove('translate-x-64');

}

// загрузка таблицы
function load_print_queue_table(page_number=null) {
    let data = {
        'search-input': document.getElementById('search-input').value,
    };
    if (page_number === null) {
        data['page_number'] = document.getElementById('print-queue-table-page-number').value;
    }
    else {
        data['page_number'] = page_number;
    }
    fetch(
        '/dashboard/print-queue-table/',
        {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: new URLSearchParams(data)
        }
    )
    .then(response => response.text())
    .then(response => {
        document.getElementById('print-queue-container').innerHTML = response;
    });
}

// Проверка что есть новые данные, если данные есть, то обновить таблицу
function check_print_queue() {
    let apiSocket = new WebSocket(
        'ws://'
        + window.location.host
        + '/api/socket/'
    );

    apiSocket.onmessage = function(e) {
        let data = JSON.parse(e.data);
        if (data.action == 'check_print_queue') {
            if (document.getElementById('print-queue-table-page-number') !== null && document.getElementById('print-queue-table-page-number').value === '1') {
                load_print_queue_table();
            }
            apiSocket.send(JSON.stringify({'action': 'check_print_queue', 'last_id': data.last_id, 'type': 'chat_message'}));
        }
    };

    apiSocket.onclose = function(e) {
        console.error('Api socket closed unexpectedly');
        check_print_queue();
    };

    apiSocket.onopen = function(e) {
        apiSocket.send(JSON.stringify({'action': 'check_print_queue', 'last_id': null, 'type': 'chat_message'}));
    };

}

// Детальное окно печати с дествиями (view, print, cancel)
function print_queue_action(print_id, action) {
    let data = {
        'print_id': print_id, 
        'action': action
    }
    if (action === 'view') {
        fetch(
            'action/',
            {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: new URLSearchParams(data)
            }
        )
        .then(response => response.text())
        .then(response => {
            document.getElementById('modal-container').innerHTML = response;
            document.getElementById('modal-container').classList.add('z-[9999]');
        });

    }
    else {
        data['amount'] = document.getElementById('print-queue-view-amount').value;

        if (document.getElementById('print-queue-view-replenishment') !== null){
            data['replenishment'] = document.getElementById('print-queue-view-replenishment').value;
        }
        fetch(
            'action/',
            {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: new URLSearchParams(data)
            }
        )
        .then(response => response.text())
        .then(response => {
            close_modal();
            load_print_queue_table();

        });

    }
}

function close_modal(){
    document.getElementById('modal-container').innerHTML='';
    document.getElementById('modal-container').classList.remove('z-[9999]');
}

// загрузка таблицы
function load_users_table(page_number=null) {
    let data = {
        'search-input': document.getElementById('search-input').value,
    };
    if (page_number === null) {
        data['page_number'] = document.getElementById('users-table-page-number').value;
    }
    else {
        data['page_number'] = page_number;
    }
    fetch(
        '/dashboard/users-table/',
        {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: new URLSearchParams(data)
        }
    )
    .then(response => response.text())
    .then(response => {
        document.getElementById('users-container').innerHTML = response;
    });
}

function show_user_actions(id) {
    let modal = document.getElementById(id);
    let active = false;
    modal.classList.remove('hidden');

    let ClickHandler = function(event) {
        if (!modal.contains(event.target) && active) {
            modal.classList.add('hidden');
            window.removeEventListener('click', ClickHandler);
        }
        else if (!active) active=true;
    };

    window.addEventListener('click', ClickHandler);
}

function users_action(user_id, action) {
    let data = {
        'user_id': user_id,
        'action': action
    }

    if (action === 'replenish_save') {
        data['amount'] = document.getElementById('users-replenish-amount').value;
        fetch(
            'action/',
            {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                body: new URLSearchParams(data)
            }
        )
        .then(response => response.text())
        .then(response => {
            close_modal();
            load_users_table();
        });
    }
    else if (action === 'view_save') {
        let data = new FormData(document.getElementById('users-view-form'));
        data.append('user_id', user_id)
        data.append('action', action)
        fetch(
            'action/',
            {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: data
            }
        )
        .then(response => response.text())
        .then(response => {
            if (response === 'user saved') {
                close_modal();
                load_users_table();
            }
            else {
                document.getElementById('modal-container').innerHTML = response;
            }
        });
    }
    else {
        fetch(
            'action/',
            {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: new URLSearchParams(data)
            }
        )
        .then(response => response.text())
        .then(response => {
            document.getElementById('modal-container').innerHTML = response;
            document.getElementById('modal-container').classList.add('z-[9999]');
        });

    }
}

function set_ready_replenish(input_id, value) {
    document.getElementById(input_id).value = value;
}

function load_cashbox_table(page_number=null) {
    let data = {
        'search-input': document.getElementById('search-input').value,
        'date-from': document.getElementById('cashbox-date-from').value,
        'date-to': document.getElementById('cashbox-date-to').value,
    };
    if (page_number === null) {
        data['page_number'] = document.getElementById('cashbox-table-page-number').value;
    }
    else {
        data['page_number'] = page_number;
    }
    fetch(
        '/dashboard/cashbox-table/',
        {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: new URLSearchParams(data)
        }
    )
    .then(response => response.text())
    .then(response => {
        document.getElementById('cashbox-container').innerHTML = response;
    });
}

function cashbox_action(cashbox_id, action) {
    let data = {
        'transaction_id': cashbox_id,
        'action': action
    }
    if (action === 'view') {
        fetch(
            'action/',
            {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                body: new URLSearchParams(data)
            }
        )
        .then(response => response.text())
        .then(response => {
            document.getElementById('modal-container').innerHTML = response;
            document.getElementById('modal-container').classList.add('z-[9999]');
            document.getElementById('cashbox-view-user').addEventListener("input", function(event) {
                cashbox_view_filter_users();
            });
            document.getElementById('cashbox-view-user').addEventListener("focusout", function(event) {
                setTimeout(function() {
                    document.getElementById('cashbox-view-user-selection').classList.add('hidden');
                }, 100);
            });
            document.getElementById('cashbox-view-user').addEventListener("focusin", function(event) {
                cashbox_view_filter_users();
            });
        });
    }
    else if (action === 'view_save') {
        data['user'] = document.getElementById('cashbox-view-user').value;
        data['type'] = document.getElementById('cashbox-view-type').value;
        data['amount'] = document.getElementById('cashbox-view-amount').value;
        fetch(
            'action/',
            {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                body: new URLSearchParams(data)
            }
        )
        .then(response => response.text())
        .then(response => {
            close_modal();
            load_cashbox_table();
        });
    }
}

function cashbox_view_filter_users() {
    let user = document.getElementById('cashbox-view-user');
    let users = document.getElementById('cashbox-view-users').value.split('___');
    let users_selection = document.getElementById('cashbox-view-user-selection');
    users_selection.innerHTML = '';
    users_selection.classList.remove('hidden');

    for (let i = 0; i < users.length; i++){
        if (users[i].toLowerCase().includes(user.value.toLowerCase()) || user.value === '') {
            let item = document.createElement('li');
            item.classList.add('text-base', 'font-normal', 'text-gray-900', 'hover:bg-indigo-400', 'hover:bg-opacity-30', 'cursor-pointer')
            item.innerText = users[i];
            users_selection.appendChild(item);
            item.onclick = function() {
                    user.value = users[i];
                    users_selection.classList.add('hidden'); 
                    users_selection.innerHTML = ''; 
                }
        }
    }

}

function check_cashbox() {
    let apiSocket = new WebSocket(
        'ws://'
        + window.location.host
        + '/api/socket/'
    );

    apiSocket.onmessage = function(e) {
        let data = JSON.parse(e.data);
        if (data.action == 'check_transactions') {
            if (document.getElementById('cashbox-table-page-number') !== null && document.getElementById('cashbox-table-page-number').value === '1') {
                load_cashbox_table()    ;
            }
            apiSocket.send(JSON.stringify({'action': 'check_transactions', 'last_id': data.last_id, 'type': 'chat_message'}));
        }
    };

    apiSocket.onclose = function(e) {
        console.error('Api socket closed unexpectedly');
        check_cashbox();
    };

    apiSocket.onopen = function(e) {
        apiSocket.send(JSON.stringify({'action': 'check_transactions', 'last_id': null, 'type': 'chat_message'}));
    };
}


function load_prices_table(page_number=null) {
    let data = {
        'search-input': document.getElementById('search-input').value,
    };
    if (page_number === null) {
        data['page_number'] = document.getElementById('prices-table-page-number').value;
    }
    else {
        data['page_number'] = page_number;
    }
    fetch(
        '/dashboard/prices-table/',
        {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: new URLSearchParams(data)
        }
    )
    .then(response => response.text())
    .then(response => {
        document.getElementById('prices-container').innerHTML = response;
    });
}

function prices_action(price_id, action) {
    let data = {
        'price_id': price_id,
        'action': action
    }

    if (action === 'view') {
        fetch(
            'action/',
            {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                body: new URLSearchParams(data)
            }
        )
        .then(response => response.text())
        .then(response => {
            document.getElementById('modal-container').innerHTML = response;
            document.getElementById('modal-container').classList.add('z-[9999]');
        });
    }
    else if (action === 'view_save') {
        data['start_page'] = document.getElementById('prices-view-start-page').value;
        data['end_page'] = document.getElementById('prices-view-end-page').value;
        data['price'] = document.getElementById('prices-view-price').value;
        fetch(
            'action/',
            {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                body: new URLSearchParams(data)
            }
        )
        .then(response => response.text())
        .then(response => {
            close_modal();
            load_prices_table();
        });
    }
    else {
        fetch(
            'action/',
            {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                body: new URLSearchParams(data)
            }
        )
        .then(response => response.text())
        .then(response => {
            close_modal();
            load_prices_table();
        });
    }
}

function load_kiosks_table() {
    let data = {
        'search-input': document.getElementById('search-input').value,
    };
    fetch(
        '/dashboard/kiosks-table/',
        {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: new URLSearchParams(data)
        }
    )
    .then(response => response.text())
    .then(response => {
        document.getElementById('kiosks-container').innerHTML = response;
    });        
}

function kiosks_action(user_id, action) {
    let data = {
        'kiosk_id': user_id,
        'action': action
    }

    if (action === 'view') {
        fetch(
            'action/',
            {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                body: new URLSearchParams(data)
            }
        )
        .then(response => response.text())
        .then(response => {
            document.getElementById('modal-container').innerHTML = response;
            document.getElementById('modal-container').classList.add('z-[9999]');
        });
    }
    else if (action === 'view_save') {
        data['name'] = document.getElementById('kiosks-view-name').value;
        data['key'] = document.getElementById('kiosks-view-key').value;
        fetch(
            'action/',
            {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                body: new URLSearchParams(data)
            }
        )
        .then(response => response.text())
        .then(response => {
            close_modal();
            load_kiosks_table();
        });
    }
    else {
        fetch(
            'action/',
            {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: new URLSearchParams(data)
            }
        )
        .then(response => response.text())
        .then(response => {
            load_kiosks_table();
        });

    }
}

function load_statistics_page() {
    let data = {
        'date_from': document.getElementById('cashbox-date-from').value,
        'date_to': document.getElementById('cashbox-date-to').value
    };
    fetch(
        '/dashboard/statistics-page/',
        {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: new URLSearchParams(data)
        }
    )
    .then(response => response.text())
    .then(response => {
        document.getElementById('statistics-container').innerHTML = response;
    });
}
// Чтение куки
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}


function load_statistics_chars() {
    let printouts_cart = document.getElementById('printouts');
    let incomes_cart = document.getElementById('incomes');
    let print_per_days_cart = document.getElementById('print_per_days');
    let income_per_days_cart = document.getElementById('income_per_days');
    let popular_printer_settings_chart = document.getElementById('popular_printer_settings');

    new Chart(printouts_cart, {
        type: 'pie',
        data: {
            labels: document.getElementById('printouts_labels').value.split('~~~'),
            datasets: [{
            data: document.getElementById('printouts_values').value.split('~~~'),
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });

    new Chart(incomes_cart, {
        type: 'pie',
        data: {
            labels: document.getElementById('incomes_labels').value.split('~~~'),
            datasets: [{
            data: document.getElementById('incomes_values').value.split('~~~'),
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });

    new Chart(print_per_days_cart, {
        type: 'line',
        data: {
            labels: document.getElementById('print_per_days_labels').value.split('~~~'),
            datasets: [
                { 
                    data: document.getElementById('print_per_days_registered_users_data').value.split('~~~'),
                    label: document.getElementById('printouts_labels').value.split('~~~')[0]
                },
                { 
                    data: document.getElementById('print_per_days_guests_data').value.split('~~~'),
                    label: document.getElementById('printouts_labels').value.split('~~~')[1]
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });

    new Chart(income_per_days_cart, {
        type: 'line',
        data: {
            labels: document.getElementById('income_per_days_labels').value.split('~~~'),
            datasets: [
                {
                data: document.getElementById('income_per_days_registered_users_data').value.split('~~~'),
                label: document.getElementById('printouts_labels').value.split('~~~')[0]
            },
            { 
                data: document.getElementById('income_per_days_guests_data').value.split('~~~'),
                label: document.getElementById('printouts_labels').value.split('~~~')[1]
            }
        ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });

    new Chart(popular_printer_settings_chart, {
        type: 'bar',
        data: {
            labels: document.getElementById('popular_printer_settings_labels').value.split('~~~'),
            datasets: [
                {
                data: document.getElementById('popular_printer_settings_data').value.split('~~~'),
                labels: document.getElementById('popular_printer_settings_labels').value.split('~~~'),
            },
        ]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                  beginAtZero: true
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}