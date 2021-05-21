var div_id = 2;

function addSimpleObjectAria() {
    let place = document.getElementById('create_div');
    let html = '<div class="col">' +
        '<label for="id_simple_object_'+ div_id + '">Простой объект:</label>' +
        '<select name="simple_object" class="form-control" id="id_simple_object_'+ div_id + '" required="">' +
        '<option value="" selected="">---------</option>' +
        // '\n' +
        // '  <option value="11">test 2_form</option>' +
        // '\n' +
        // '  <option value="14">Кабель UTP-5E</option>' +
        // '\n' +
        // '  <option value="1">Комплектующая-1</option>' +
        // '\n' +
        // '  <option value="2">Комплектующая-2</option>' +
        // '\n' +
        // '  <option value="3">Комплектующая-3</option>' +
        // '\n' +
        // '  <option value="4">Компьютер</option>' +
        // '\n' +
        // '  <option value="12">Монитор GTYGVFR-56473</option>' +
        // '\n' +
        // '  <option value="8">Мультиметр цифровой Uni Trend</option>' +
        // '\n' +
        // '  <option value="9">Объектив EC Plan-Neofluar 1x/0/025 M27</option>' +
        // '\n' +
        // '  <option value="13">Саморезы</option>\n' +
        // '\n' +
        // '  <option value="7">Схема 1</option>\n' +
        // '\n' +
        // '</select>\n' +
        '            </div><div class="col col-lg-2">' +
        '<label for="id_simple_object_' + div_id + '_amount">Количество:</label>' +
        '<input type="number" name="simple_object_amount" class="form-control" placeholder="Количество" id="id_simple_object_' + div_id + '_amount" required="">' +
        '</div>';
    place.insertAdjacentHTML('beforebegin', html);
    console.log(div_dict);
    div_dict.push(div_id);
    div_id = div_id + 1;
}

