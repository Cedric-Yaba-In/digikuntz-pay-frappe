// Copyright (c) 2025, GIC Promote Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on("ApiKey", {
	async refresh(frm) {
        let defaultApiKey = await frappe.db.get_list("ApiKey",{
            filters: {default:1},
            fields: ["*"]
        }
    )
        console.log("DefaultApiKey",defaultApiKey);
	},
    // async validate(frm) {
    //     if(frm.doc.default)
    //     {
    //         let defaultApiKey = await frappe.db.get_value("ApiKey",{enable:1})
    //     }
    //     console.log("frm ",frm.doc)
    // }
    before_save: function (frm) {
        return new Promise(async (resolve,reject)=>{
            if(!frm.doc.default) return resolve(); //Si pas définit comme passerelle par défault alors on sauvegarde

            let defaultApiKey = await frappe.db.get_list("ApiKey",{
                filters: {default:1},
                fields: ["*"]
                });
            
            frm.set_value("enable",1); // Au cas ou ce n'est pas activé

            if(defaultApiKey.length==0) return resolve(); //si c'est le premier composant pas défaut: 
            //Si on a choisi la nouvelle clefs comme celle par défaut alors on retire celle qui à été mis précédement comme defaut

            frappe.confirm(
                __("Voulez-vous vraiment changer la passerelle par défault?"),
                async ()=>{
                    await frappe.db.set_value("ApiKey",defaultApiKey[0].name,'default',0);
                    resolve();
                },
                ()=>reject()
            )            
        })
    },
});
