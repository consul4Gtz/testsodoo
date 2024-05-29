/** @odoo-module **/

import { registry } from "@web/core/registry";
import { usePopover } from "@web/core/popover/popover_hook";
import { useService } from "@web/core/utils/hooks";
import { parseDate, formatDate } from "@web/core/l10n/dates";

import { formatMonetary } from "@web/views/fields/formatters";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
const { Component, onWillUpdateProps } = owl;

class AccountWhtaxPopOver extends Component {}
AccountWhtaxPopOver.template = "l10n_hn_edi.AccountWhtaxPopOver";

export class AccountWhtaxField extends Component {
    //props del componente
    static props = { ...standardFieldProps };
    setup() {
        this.popover = usePopover();
        this.orm = useService("orm");
        this.action = useService("action");

        this.formatData(this.props);
        onWillUpdateProps((nextProps) => this.formatData(nextProps));
    }

    formatData(props) {
        //const info = props.value || {
        const info = props.record.data[this.props.name] || {
            content: [],
            outstanding: false,
            title: "",
            move_id: this.props.record.data.id,
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
    }

}
AccountWhtaxField.template = "l10n_hn_edi.AccountWhtaxField";

export const accountwhtaxField = {
    component: AccountWhtaxField,
    supportedTypes: ["char"],
};

registry.category("fields").add("whtax", accountwhtaxField);
