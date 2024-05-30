/** @odoo-module **/

import { Component, useState } from '@odoo/owl';
import { registry } from "@web/core/registry";
//import { xml } from '@odoo/owl/tags';
//import { Component } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class MyOwlWidget extends Component {
   //this.state = useState({ value: 1 });
    static props = { ...standardFieldProps };
    setup() {
        this.state = useState({
           // value: this.props.value,
           value: 1,
        });
        //console.log("MyOwlWidget.setup");
        console.log(this.state.value);
        //console.log(this.props.record.data);
    }
}
MyOwlWidget.template = "l10n_hn_edi.testfield";

export const accounttestField = {
    component: MyOwlWidget,
    supportedTypes: ["char"],
};
//MyOwlWidget.supportedTypes = ["char"];
registry.category("fields").add('my_owl_widget', accounttestField);