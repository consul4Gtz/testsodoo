/** @odoo-module **/

//importar el registro de campos -prueba
//import fieldRegistry from 'web.field_registry_owl';
import { registry } from "@web/core/registry";
import { usePopover } from "@web/core/popover/popover_hook";
import { useService } from "@web/core/utils/hooks";
import { parseDate, formatDate } from "@web/core/l10n/dates";

import { formatMonetary } from "@web/views/fields/formatters";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

const { Component, onWillRender } = owl;

class AccountWhtaxPopOver extends Component {}
AccountWhtaxPopOver.props = {
    "*": { optional: true },
}
AccountWhtaxPopOver.template = "l10n_hn_edi.AccountWhtaxPopOver";

export class AccountWhtaxField extends Component {
   // Definir las propiedades estáticas (props)
    //static props = { ...standardFieldProps };
    static props = {
        value: { type: Object, optional: true },
        record: { type: Object, optional: false },
        readonly: { type: Boolean, optional: true },
        id: { type: [Number, String], optional: true },
        name: { type: String, optional: true },
    };
    
    setup() {
         
        this.popover = usePopover();
        this.orm = useService("orm");
        this.action = useService("action");
        //pruebas para revisar el valor de las propiedades
        console.log(this.props.record.data);
        console.log("tomar_data")
        //console.log(this.formatData());
        console.log(this.props.record.data[this.props.name]);
    
        //this.formatData(this.props);
       //onWillUpdateProps(() =>{console.log("onWillUpdateProps")});
        //this.formatData(this.props);
        //onWillUpdateProps((nextProps) => this.formatData(nextProps));
        //onWillUpdateProps((nextProps) => { this.formatData(nextProps);
        //console.log("onwill");
        //});
        //el metodo se ejecuta antes de renderizar
        //se omite la declaracion de la funcion para que se ejecute en el momento de la creacion del componente, 
        //especificamente en el setup previo a la renderizacion
        onWillRender(() =>{ this.formatData(this.props)
            console.log("onWillRender");
        });
    
    }

    formatData(props) {
        const info = props.record.data[this.props.name] || {
        //const info = this.props.record.data[this.props.name] || {
            content: [],
            outstanding: false,
            title: "",
            move_id: this.props.record.resId,
            //move_id: this.props.record.data.id,
        };
        for (let [key, value] of Object.entries(info.content)) {
            value.index = key;
            value.amount_formatted = formatMonetary(value.amount, { currencyId: value.currency_id });
            if (value.date) {
                value.date = formatDate(parseDate(value.date));
            }
        }
        this.lines = info.content;
        this.title = info.title;
        this.move_id = info.move_id;
        console.log("En el formateo");
        console.log(info.title);
        console.log(props.record.data[this.props.name]);
    }
    //prueba de funciones para el manejo de los datos
   /*  formatData(){
        try {
           const info = this.props.record.data[this.props.name] || {
            //const info = props.value || {
                   content: [],
                   outstanding: false,
                   title: "",
                   //move_id: this.props.record.resId,
                   move_id: this.props.record.data.id,
                };
            for (const [key, value] of Object.entries(info.content)) {
                value.index = key;
                value.amount_formatted = formatMonetary(value.amount, {
                    currencyId: value.currency_id,
                });
                   if (value.date) {
                       // value.date is a string, parse to date and format to the users date format
                       value.date = formatDate(parseDate(value.date));
                   }
                }
                console.log(info);
            return {
                lines: info.content,
                outstanding: info.outstanding,
                title: info.title,
                moveId: info.move_id,
            };
            
        } catch (error) {
            console.log("Error en formatData");
        }
    } */
}
//hacemos referencia a la plantilla que se va a utilizar
AccountWhtaxField.template = "l10n_hn_edi.AccountWhtaxField";

//registramos el campo en el registro de campos de esta forma se puede utilizar en cualquier vista
export const accountwhtaxField = {
    component: AccountWhtaxField,
    supportedTypes: ["char"],
};

registry.category("fields").add("whtax", accountwhtaxField);
//fieldRegistry.add("whtax", AccountWhtaxField);
