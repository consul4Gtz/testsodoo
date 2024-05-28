/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState } from "@odoo/owl";

class ContadorCaracteresWidget extends Component {
    setup() {
        this.state = useState({
            count: this.props.record.data[this.props.name].length || 0
        });
    }

    onInput(event) {
        this.state.count = event.target.value.length;
        this.props.record.update({ [this.props.name]: event.target.value });
    }
}

ContadorCaracteresWidget.template = 'mi_modulo.ContadorCaracteresTemplate';
registry.category('fields').add('contador_caracteres', ContadorCaracteresWidget);