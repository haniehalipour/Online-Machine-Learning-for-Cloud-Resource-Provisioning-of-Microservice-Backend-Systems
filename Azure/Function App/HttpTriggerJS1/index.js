module.exports = function (context, req) {
    //context.log('reza');
    //context.done();
    //return true;

    var temp_current_api = req.originalUrl;
    if (temp_current_api.indexOf("?") > 0) {
        temp_current_api = temp_current_api.substring(0, temp_current_api.indexOf("?"))

        if (req.query.code || (req.body && req.body.code)) {
            var code = req.query.code ? req.query.code : req.body.code;
        }

        if (code) {
            temp_current_api = temp_current_api + "?code=" + code;
        }
    }
    const current_api = temp_current_api;

    //const current_api = 'https://test-new-code-reza.azurewebsites.net/api/HttpTriggerJS1?code=KyMnCz8jpUCyfwXOuL3yLi0yykkfnOqFyF6jakJ67EVJXMukg/DiAQ==';
	const ml_api = 'http://40.117.72.182/api/';//'http://18.206.161.123/aws/'; //const ml_api = 'http://104.40.193.35/scikit.py';
	const grafana_API = 'http://40.117.85.133:3000/api/datasources/proxy/2/api/v1/query_range?query=';
	const add_remove_resources_api = 'http://40.117.72.182/api/';
	const NdbenchAPI = 'http://52.234.213.114:8080/';//'http://18.209.34.140:8080/'
    const containerName = 'test-container';
	const dataset_blobName = 'dataset.csv';
	const ML_model_config_file_name = 'ML_model.json';
	const dataset_config_file_name = 'dataset_config.json';
	const storage_account_name = 'testresourcegroup234';
	const access_key = 'mf5gWutfe20854/lqyu+FRpXg1GVt1errPEdAZidfRfezOPJ0M+WtA136N1P3sz7cDJFAqlcHfhkv8j8j6Y5Cw==';
    //We are not using Azure Storage Tables. because it is so buggy!
    //we did prefer to save our data on the Blob storage as a json file.
    const blob_database = 'database.json';
	// host_ip is the IP of DevOps Instance
	const host_ip = '40.87.66.25'
	
    const req_handler = require('http');
    const req_handler_https = require("https");
	//require('dotenv').load();
	//const path = require('path');
	//const args = require('yargs').argv;
	const storage = require('azure-storage');
	const blobService = storage.createBlobService(storage_account_name, access_key);

    if (req.query.task || (req.body && req.body.task))
    {
        const task = req.query.task ? req.query.task : req.body.task;

        if (task == 'build_model') {
            //###################
            //## Configuration ##
            //###################
            let for_last_n_minutes = 10;
            if (req.query.for_last_n_minutes || (req.body && req.body.for_last_n_minutes))
            {
                for_last_n_minutes = parseInt(req.query.for_last_n_minutes ? req.query.for_last_n_minutes : req.body.for_last_n_minutes);
            }
            
            //############################
            //## SET START AND END TIME ##
            //############################
            //we need to set time period in "timestamp" format
            let date = new Date();
            //set "end_time" to one minute ago to make sure that metrics are collected
            //then "end_time" is current time minus one minute
            let end_time = Math.floor(date.getTime() / 1000) - 60;
            //we want to collect metrics for 10 minutes.
            //then "start_time" will be end_time - 10minutes
            let start_time = end_time - (for_last_n_minutes * 60);

            //let collected_metrics = get_metrics (start_time, end_time);
			
			var collected_metrics = get_metrics (start_time, end_time);
            
            //context.done();
            //return false;
			collected_metrics.then(function(result) {
                
				var normilized_dataset = normilize (result);
                
                context.log('dataset is normilized now');
				/*upload_dataset (normilized_dataset, function(uploading_result){
                    context.log(uploading_result);
                    context.done();
                });*/
				
                var uploading_result = upload_dataset (normilized_dataset);
                
				uploading_result.then(function(uploaded_dataset_config_url) {
					//##################
					//## create model ##
					//##################
                    
					let machine_learning_api = ml_api+"?task=build_model&config_url="+uploaded_dataset_config_url+"&callback_api="+current_api;
					req_handler.get(machine_learning_api, (resp) => {
						let data = '';

						// A chunk of data has been recieved.
						resp.on('data', (chunk) => {
							data += chunk;
						});

						// The whole response has been received. Print out the result.
						resp.on('end', () => {
                            /*context.log('reza15');
                    context.done();
                    return false;*/
							//########################
							//## ML MODE is Created ##
							//########################
							//Creating the models will take several times and mostly it will get timeout error
							//then we don't wait for it's result and we will CallBack current FunctionApp from the ML-API
							context.log("## Machine Learning Response ##");
							context.log(data);
							
							context.done();
						});

					}).on("error", (err) => {
						context.log("Error: " + err.message);
						reject(err);
						context.done();
						//return false;
					});
					
					
					//context.log(result2);
                    context.done();
					
				}, function(err) {
					context.log(err);
				});
				
				context.done();
				
			}, function(err) {
				context.log(err);
			});
        }
        else if (task == 'save_models_result') {
			//r = requests.get(callback_api, params={"task": "save_models_result", "selected_model": best_model, "model_id": best_model_id, "model_params": best_model_params})
			const selected_model = req.query.selected_model ? req.query.selected_model : req.body.selected_model;
			const model_id = req.query.model_id ? req.query.model_id : req.body.model_id;
			const model_params = req.query.model_params ? req.query.model_params : req.body.model_params;
			
			//ML_model_config_file_name = 'ML_model.json';
			ml_model_config = '{"selected_model": "'+selected_model+'", "model_id": "'+model_id+'", "params":'+model_params+'}';
			
			//#################################
			//## Start Uploading Config File ##
			//#################################
			blobService.createBlockBlobFromText(
			containerName,
			ML_model_config_file_name,
			ml_model_config,
			function(error, result, response)
			{
				if(error)
				{
					context.log("Couldn't upload ML_MODEL config");
					context.error(error);
					context.done();
					return false;
				}
				else
				{
					context.log('ML_MODEL Config File uploaded successfully');
					context.done();
				}
			});
        }
        else if (task == 'add_resource') {
            req_handler.get(add_remove_resources_api + "?task=add_new_resource&host_ip="+host_ip+"&callback_api="+current_api, (resp) => {
                let data = '';

            // A chunk of data has been recieved.
            resp.on('data', (chunk) => {
                data += chunk;
            });
                
                // The whole response has been received. Print out the result.
                resp.on('end', () => {
                    context.log("'Add resource' request has been sent. you need to wait for it's response.");
                context.done();
            });

            }).on("error", (err) => {
                    context.log("'Add resource' request has been failed. response code: " + err.message);
                context.done();
            });
        }
        else if (task == 'resource_is_added') {
            if (req.query.ip || (req.body && req.body.ip)) {
                var ip = req.query.ip ? req.query.ip : req.body.ip;
            }

            if (ip) {
                //Start Loading blob_database.json
                //Check to see if it is exists
                //#########################################
                //## Create Blob Container if not exists ##
                //#########################################
                var promise = new Promise(function(resolve, reject) {
                    blobService.createContainerIfNotExists(containerName, { publicAccessLevel: 'blob' }, err => {
                        if(err) {
                            context.log('Something is wrong with creating Blob Container:');
                            context.log(err);
                            reject(Error(err));
                            context.done();
                        } else {
                            //#############################
                            //## Blob container is ready ##
                            //#############################
                            context.log({ message: `Container '${containerName}' created` });
                    resolve("Stuff worked!");

                    var resource_list = [];
                    var database = {};

                    //var loaded_database = download_from_blob(blobService, containerName, blob_database)
                    blobService.getBlobProperties(
                        containerName,
                        blob_database,
                        function (err, properties, status) {
                            if (status.isSuccessful) {
                                // Blob exists
                                context.log("Start loading '" + blob_database + "'.");

                                blobService.getBlobToText(
                                    containerName,
                                    blob_database,
                                    function (err, blobContent, blob) {
                                        if (err) {
                                            context.error("Couldn't download blob %s", blob_database);
                                            context.error(err);
                                            context.done();
                                            return false;
                                        } else {
                                            context.log("Sucessfully downloaded blob %s", blob_database);
                                            var loaded_database = blobContent;
                                           // context.log(loaded_database);
                                            if (loaded_database) {
                                                loaded_database = JSON.parse(loaded_database);
                                                //context.log(loaded_database);
                                                database = loaded_database;
                                            }
                                            else
                                            {
                                                context.log(`'${blob_database}' is not exists.`);
                                            }

                                            if (database.resource_list) {
                                                resource_list = database.resource_list;
                                            }
                                            else {
                                                //There is no resource list yet
                                                //this resource will be first in the list
                                                database.resource_list = [];
                                            }

                                            if (resource_list.indexOf(ip) >= 0)
                                            {
                                                //this resource is in the list somehow,
                                                //we don't need to add it again
                                            }
                                            else
                                            {
                                                //Add new IP to the resource list
                                                resource_list.push(ip);
                                            }

                                            database.resource_list = resource_list;
                                            context.log(JSON.stringify(database));
                                            upload_to_blob(blobService, containerName, blob_database, JSON.stringify(database));

                                            context.done();
                                        }
                                        //context.done();
                                    });
                            } else {
                                // Blob doesn't exist
                                context.log("'" + blob_database + "' doesn't exist.");

                                //Start creating new one
                                var database = {};
                                database.resource_list = [];
                                database.resource_list.push(ip);

                                upload_to_blob(blobService, containerName, blob_database, JSON.stringify(database));

                                context.done();
                                return false;
                            }
                        });
                }
                });

                    //context.done();
                });
                //context.done();
            }
            else {
                context.log("We could not get the IP for recently added resource. smething is wrong with add_remove_resources_api.");
                context.done();
            }
            //context.done();
        }
        else if (task == 'remove_resource') {
            //Get current resource list
            //Check to see if it is exists
            //#########################################
            //## Create Blob Container if not exists ##
            //#########################################
            var promise = new Promise(function(resolve, reject) {
                blobService.createContainerIfNotExists(containerName, { publicAccessLevel: 'blob' }, err => {
                    if(err) {
                        context.log('Something is wrong with creating Blob Container:');
                        context.log(err);
                        reject(Error(err));
                        context.done();
                    } else {
                        //#############################
                        //## Blob container is ready ##
                        //#############################
                        context.log({ message: `Container '${containerName}' created` });
                resolve("Stuff worked!");

                var resource_list = [];
                var database = {};
                var resource_to_remove = false;

                blobService.getBlobProperties(
                    containerName,
                    blob_database,
                    function (err, properties, status) {
                        if (status.isSuccessful) {
                            // Blob exists
                            context.log("Start loading '" + blob_database + "'.");

                            blobService.getBlobToText(
                                containerName,
                                blob_database,
                                function (err, blobContent, blob) {
                                    if (err) {
                                        context.error("Couldn't download blob %s", blob_database);
                                        context.error(err);
                                        context.done();
                                        return false;
                                    } else {
                                        context.log("Sucessfully downloaded blob %s", blob_database);
                                        var loaded_database = blobContent;
                                        //context.log(loaded_database);
                                        if (loaded_database) {
                                            database = JSON.parse(loaded_database);
                                        }
                                        else
                                        {
                                            context.log(`'${blob_database}' is not exists.`);
                                        }

                                        if (database.resource_list) {
                                            resource_list = database.resource_list;
                                        }
                                        else {
                                            //There is no resource list yet
                                            //this resource will be first in the list
                                            //database.resource_list = [];
                                        }

                                        if (resource_list.length > 0)
                                        {
                                            //there is at least one resource in the list
                                            //we need to pop it and request to remove for last added resource
                                            latest_added_resource = resource_list.pop();
                                            //Send request to ADD/Remove API
                                            req_handler.get(add_remove_resources_api + "?task=remove_resource&resource_ip="+latest_added_resource+"&host_ip="+host_ip+"&callback_api="+current_api, (resp) => {
                                                let data = '';

                                                // A chunk of data has been recieved.
                                                resp.on('data', (chunk) => {
                                                    data += chunk;
                                            });

                                                // The whole response has been received. Print out the result.
                                                resp.on('end', () => {
                                                    context.log(`'Remove resource' request has been sent for '${latest_added_resource}'. you need to wait for it's response.`);
                                                //context.done();
                                            //return true;
                                            });

                                            }).on("error", (err) => {
                                                context.log("'Remove resource' request has been failed. response code: " + err.message);
                                                //context.done();
                                            //return true;
                                            });
                                        }
                                        else
                                        {
                                            //the resource list is empty and there is no more resource to remove
                                            context.log("The resource list is empty and there is no more resource to remove.");
                                            //context.done();
                                            //return true;
                                        }

                                        //database.resource_list = resource_list;
                                        //context.log(JSON.stringify(database));
                                        //upload_to_blob(blobService, containerName, blob_database, JSON.stringify(database));

                                        context.done();
                                    }
                                    //context.done();
                                });
                        } else {
                            // Blob doesn't exist
                            context.log("'" + blob_database + "' doesn't exist.");
                            context.log("The resource list is empty (it doesn't exist), then there is no more resource to remove.");
                            context.done();
                            return false;
                        }
                    });
            }
            });

                //context.done();
            });
        }
		else if (task == 'resource_is_removed') {
			if (req.query.ip || (req.body && req.body.ip)) {
                var ip = req.query.ip ? req.query.ip : req.body.ip;
            }
			
            if (ip) {
                //Start Loading blob_database.json
                //Check to see if it is exists
                //#########################################
                //## Create Blob Container if not exists ##
                //#########################################
                var promise = new Promise(function(resolve, reject) {
                    blobService.createContainerIfNotExists(containerName, { publicAccessLevel: 'blob' }, err => {
                        if(err)
						{
                            context.log('Something is wrong with creating Blob Container:');
                            context.log(err);
                            reject(Error(err));
                            context.done();
                        }
						else
						{
                            //#############################
                            //## Blob container is ready ##
                            //#############################
                            context.log({ message: `Container '${containerName}' created` });
							resolve("Stuff worked!");

							var resource_list = [];
							var database = {};
							
							//var loaded_database = download_from_blob(blobService, containerName, blob_database)
							blobService.getBlobProperties(
							containerName,
							blob_database,
							function (err, properties, status) {
								if (status.isSuccessful) {
									// Blob exists
									context.log("Start loading '" + blob_database + "'.");
									blobService.getBlobToText(
										containerName,
										blob_database,
										function (err, blobContent, blob) {
											if (err) {
												context.error("Couldn't download blob %s", blob_database);
												context.error(err);
												context.done();
												return false;
											} else {
												context.log("Sucessfully downloaded blob %s", blob_database);
												var loaded_database = blobContent;
											   // context.log(loaded_database);
												if (loaded_database) {
													loaded_database = JSON.parse(loaded_database);
													//context.log(loaded_database);
													database = loaded_database;
												}
												else
												{
													context.log(`'${blob_database}' is not exists.`);
												}

												if (database.resource_list) {
													resource_list = database.resource_list;
												}
												else {
													//There is no resource list yet
													//this resource will be first in the list
													database.resource_list = [];
												}

												if (resource_list.indexOf(ip) >= 0)
												{
													//this resource is in the list somehow,
													//We will update the DB
													//resource_list = resource_list.split("::NEW_RESOURCE::")
													
													//Remove recently removed resource from the list
													for (var i = 0; i < resource_list.length; i++) {
														if ( resource_list[i] === ip) {
															resource_list.splice(i, 1);
														}
													}
												}
												else
												{
													//removed resource is not in the list
													//we don't need to do anything more
												}

												database.resource_list = resource_list;
												context.log(`resource '${ip}' removed from the resource list`);
												upload_to_blob(blobService, containerName, blob_database, JSON.stringify(database));

												context.done();
											}
											//context.done();
										});
								} else {
									// Blob doesn't exist
									context.log("'" + blob_database + "' doesn't exist.");

									//Start creating new one
									var database = {};
									database.resource_list = [];

									upload_to_blob(blobService, containerName, blob_database, JSON.stringify(database));

									context.done();
									return false;
								}
							});
						}
					});

                    //context.done();
                });
                //context.done();
            }
            else {
                context.log("We could not get the IP for recently removed resource.");
                context.done();
            }
        }
		else if (task == 'predict') {
            //###################
            //## Configuration ##
            //###################
            let for_last_n_minutes = 10;
            if (req.query.for_last_n_minutes || (req.body && req.body.for_last_n_minutes))
            {
                for_last_n_minutes = parseInt(req.query.for_last_n_minutes ? req.query.for_last_n_minutes : req.body.for_last_n_minutes);
            }

            //############################
            //## SET START AND END TIME ##
            //############################
            //we need to set time period in "timestamp" format
            let date = new Date();
            //set "end_time" to one minute ago to make sure that metrics are collected
            //then "end_time" is current time minus one minute
            let end_time = Math.floor(date.getTime() / 1000) - 60;
            //we want to collect metrics for 10 minutes.
            //then "start_time" will be end_time - 10minutes
            let start_time = end_time - (for_last_n_minutes * 60);

            //########################
            //## Load ML_model.json ##
            //########################
            //https://testresourcegroup234.blob.core.windows.net/test-container/ML_model.json
            //var ML_model_config_file_name = 'ML_model.json'
            blobService.getBlobProperties(
			containerName,
			ML_model_config_file_name,
			function(err, properties, status) {
				if (status.isSuccessful) {
					// Blob exists
					context.log("Start loading '"+ML_model_config_file_name+"'.");

					blobService.getBlobToText(
					containerName,
					ML_model_config_file_name,
					function(err, blobContent, blob) {
						if (err) {
							context.error("Couldn't download blob %s", ML_model_config_file_name);
							context.error(err);
						}
						else {
							context.log("Sucessfully downloaded blob %s", ML_model_config_file_name);
							context.log(blobContent);
							//blobcontent is like this:
							/*{"selected_model": "LR", "model_id": "ski_model_LR.pkl", "params":{"penalty": "l2", "dual": false, "tol": 0.0001, "C": 1.0, "fit_intercept": true, "intercept_scaling": 1, "class_weight": null, "random_state": null, "solver": "liblinear", "max_iter": 100, "multi_class": "ovr", "verbose": 0, "warm_start": false, "n_jobs": 1}}*/
							var ML_model_config = JSON.parse(blobContent);

							var collected_metrics = get_metrics (start_time, end_time);
							collected_metrics.then(function(result) {
								var normilized_dataset = normilize (result);
								context.log('dataset is normilized now');

								var predict_data_array = [];
								var predict_data_query_string = "";
								for (var key in normilized_dataset) {
									var temp_query_str = normilized_dataset[key]['cpu']+","+normilized_dataset[key]['memory']+","+normilized_dataset[key]['network_in']+","+normilized_dataset[key]['network_out'];
									predict_data_array.push({"original_metrics": normilized_dataset[key], "query_string": temp_query_str})
									if (predict_data_query_string == "")
									{
										predict_data_query_string += "predict_data[]="+temp_query_str;
									}
									else
									{
										predict_data_query_string += "&predict_data[]="+temp_query_str;
									}
								}

								//context.log(predict_data_array);

								var predict_url = ml_api+"?task=predict&model_id="+ML_model_config['model_id']+"&"+predict_data_query_string;

								req_handler.get(predict_url, (resp) => {
									let data = '';
									// A chunk of data has been recieved.
									resp.on('data', (chunk) => {
										data += chunk;
									});
									// The whole response has been received. Print out the result.
									resp.on('end', () => {
										//predict_for_current["original_metrics"]["predicted_as"] = JSON.parse(data);
										/*
										predicted_row include:
										{
											date: '2018-7-8',
											time: '13:19',
											network_in: 411.39567057276145,
											network_out: 367.1936944699846,
											cpu: 2.4902880554160824,
											memory: 6.638251507641998,
											final_target: 5.319979191468996,
											final_class: 1,
											predicted_as: 5.321684271605829
										}
										*/

										var temp_predicted_results = JSON.parse(data);
										var predicted_results = [];
										temp_predicted_results.forEach(function (val, idx) {
											predict_data_array[idx]["original_metrics"]["predicted_as"] = val;
											predicted_results.push(predict_data_array[idx]["original_metrics"]);
										});
										
										//prediction_result = json.loads(r.content)
										//for idx, val in enumerate(prediction_result):
										//predict_data_array[idx]["original_metrics"]["predicted_as"] = val

										//###############################
										//## ALL METRICS ARE PREDICTED ##
										//###############################
										//Start predicting future
										blobService.getBlobProperties(
											containerName,
											dataset_blobName,
											function(err, properties, status) {
												if (status.isSuccessful) {
													// Blob exists
													/*
													###################################################
													## Load Original DataSet (saved on blob storage) ##
													###################################################
													*/
													context.log("Start loading '"+dataset_blobName+"'.");

													blobService.getBlobToText(
														containerName,
														dataset_blobName,
														function(err, blobContent, blob) {
															if (err) {
																context.error("Couldn't download blob %s", dataset_blobName);
																context.error(err);
															}
															else {
																context.log("Sucessfully downloaded blob %s", dataset_blobName);
																//context.log(blobContent);
																//blobcontent is Our DATASET and it is like this:
																/*
																date,time,cpu,memory,network_in,network_out,final_target,final_class
																2018-6-25,10:47,1.6105938308332193,6.263709941406065,471.270104449708,429.58427097508684,4.933170181147739,1
																...
																2018-6-25,10:49,1.53407241749998,6.238672886008315,481.25877844775096,434.9773373808712,4.896015506041561,1
																*/
																var dataset = blobContent;//JSON.parse(blobContent);
																var dataset_array = dataset.split("\r\n");
																var delimiters = ",";
																var has_header = true;
																var header = [];
																var csv = [];

																for (var dataset_index = 0; dataset_index < dataset_array.length; dataset_index++) {
																	var dataset_row = dataset_array[dataset_index];

																	if (dataset_row !="")
																	{
																		if (dataset_index == 0 && has_header)
																		{
																			header = dataset_row.split(delimiters).map(item => item.trim());
																			//first row is header
																			continue;
																		}
																		//context.log(dataset_index);
																		var temp_row = dataset_row.split(delimiters).map(item => item.trim());

																		if (header.length > 0)
																		{
																			var temp_row_json = {};
																			//we have header then we should add each column to it's header_lable
																			header.forEach(function(header_lable, index){
																				temp_row_json[header_lable] = temp_row[index];
																			});

																			csv.push(temp_row_json);
																		}
																		else
																		{
																			csv.push(temp_row);
																		}
																	}
																	else
																	{
																		//row is empty, then we will skip this row
																	}
																}

																/*
																##################################################
																## Convert Original Dataset to a sortable array ##
																##################################################
																*/
																csv_rows = []

																csv.forEach(function(row, row_index){
																	csv_rows.push({"index":row_index, "distance": "unknown", 'statistics_holder': row});
																});

																/*
																############################
																## Load Predicted results ##
																############################
																*/
																var prediction_result = []
																predicted_results.forEach(function(predicted_row){
																	//context.log(predicted_row);
																	/*
																	predicted_row include:
																	{
																		date: '2018-7-8',
																		time: '13:19',
																		network_in: 411.39567057276145,
																		network_out: 367.1936944699846,
																		cpu: 2.4902880554160824,
																		memory: 6.638251507641998,
																		final_target: 5.319979191468996,
																		final_class: 1,
																		predicted_as: 5.321684271605829
																	}
																	*/
																	prediction_result.push(predicted_row["predicted_as"]);
																});

																/*
																Now prediction_result is something like this:
																[38.2909240722656, 43.9702110290527, 37.5441398620605, 44.5855293273925, 37.1401634216308, 39.3730659484863, 42.2084693908691, 60.3783950805664, 55.1704139709472, 41.3145446777343]
																*/

																var final_avegare_of_prediction = 0;

																prediction_result.forEach(function(PR){
																	csv_rows.forEach(function(row){
																		/*
																		######################################################
																		## Calculate Distance for recently predicted record ##
																		######################################################
																		# a sample of predicted record is like this:
																		{date: '2018-7-8',time: '13:19',network_in: 411.39567057276145,network_out: 367.1936944699846,cpu: 2.4902880554160824,memory: 6.638251507641998,final_target: 5.319979191468996,final_class: 1,predicted_as: 5.321684271605829}

																		csv_rows[0] is something like:
																		{ index: 0, distance: 'unknown', statistics_holder: {date: '2018-7-7',time: '8:54',cpu: '2.455948978750561',memory: '6.573060684153517',network_in: '428.7891295189038',network_out: '379.7656154257711',final_target: '5.266728943322991',final_class: '1'}}
																		*/

																		var pr_tar = parseFloat(PR);//predicted target
																		var row_tar = parseFloat(row['statistics_holder']["final_target"]);//original csv saved row target
																		//context.log("pr_tar: '"+pr_tar+", row_tar: '"+row_tar+"'");
																		var distance = Math.sqrt( Math.pow(pr_tar - row_tar, 2) );
																		//context.log("distance: "+distance);
																		csv_rows[row['index']]['distance'] = distance;
																	});

																	//context.log("Row:")
																	//context.log(csv_rows);

																	/*
																	############################
																	## Calculate max distance ##
																	############################
																	*/
																	var percent_of_calculation = 0.25; //25%

																	//sort by distance
																	//We should not change the order of csv_rows
																	//then we need to clone it. simplest way to clone is slice with 0!
																	//to know more follow the link:
																	//https://davidwalsh.name/javascript-clone-array
																	var temp_to_sort = csv_rows.slice(0);
																	var sorted_rows_by_distance = temp_to_sort.sort(function(a,b) {return (a.distance > b.distance) ? 1 : ((b.distance > a.distance) ? -1 : 0);} );

																	//calculate maximum defference minimum and maximum distance
																	var deff = sorted_rows_by_distance[sorted_rows_by_distance.length - 1]["distance"] - sorted_rows_by_distance[0]["distance"];
																	//context.log("deffdeffdeffdeffdeffdeffdeffdeffdeffdeff:" + deff);
																	max_dist = deff * percent_of_calculation;

																	/*
																	#####################
																	## Index Neighbors ##
																	#####################
																	*/
																	var index_of_neighbors = [];
																	//context.log("max_dist: " + max_dist);
																	csv_rows.forEach(function(row){
																		//context.log("csv_rows[row['index']]['distance'] " +csv_rows[row['index']]['distance']+ " ,max_dist: " + max_dist);
																		if (csv_rows[row['index']]['distance'] <= max_dist)
																		{
																			//this record is neighbor
																			index_of_neighbors.push(row['index']);
																		}
																	});
																	
																	/*
																	##########################################################
																	## Calculate average for each Neighbors in future_steps ##
																	##########################################################
																	*/
																	// I want to know what is the average of distance for each neighbor in future
																	// and I have future_steps as a limit to calculate for future.
																	var future_steps = for_last_n_minutes;
																	var neighbor_averages = [];

																	index_of_neighbors.forEach(function(neighbor){
																		// then, here, 'neighbor' is index of the row in original dataset
																		//var average = 0;
																		var nei = csv_rows[neighbor]['statistics_holder']; // neighbor index => nei
																		//csv_rows[0] is something like:
																		/*
																		{ index: 0, distance: 0.13451984639433245, statistics_holder: { date: '2018-7-7', time: '9:6', cpu: memory: network_in: '574.1186906404328', network_out: '536.4099839152768', final_target: '5.146922356862906', final_class: '1' } }
																		*/

																		//console.log("nei: ")
																		//console.log(nei);
																		//context.done();
																		//return true;
																		try {
																			//context.log(parseFloat(nei["final_target"]));
																			var nei_tar = parseFloat(nei["final_target"]);
																			var row_tar = parseFloat(csv_rows[neighbor + future_steps]['statistics_holder']["final_target"]);

																			//distance = math.sqrt( math.pow(nei_cpu - r_cpu, 2) + math.pow(nei_mem - r_mem, 2) + math.pow(nei_ni - r_ni, 2) + math.pow(nei_no - r_no, 2) + math.pow(nei_tar - row_tar, 2) )
																			var distance = row_tar - nei_tar;
																			//print ("distance of P" + str(neighbor + 10) + " => " + str(distance))
																			//average += distance
																			neighbor_averages.push(distance);
																		}
																		catch(err) {
																			// context.log("Current point is '"+neighbor+"'    Next retrieved point is '"+neighbor + next_index+"'    Number of all points '"+csv_rows.length+"'");
																			//continue;
																		}
																		//average = average / future_steps
																	});

																	/*
																	#######################################
																	## Calculate average of all averages ##
																	#######################################
																	*/
																	var final_average = 0;
																	neighbor_averages.forEach(function(ave){
																		final_average += ave;
																	});
																	//context.log("final_average aval: "+final_average + " , neighbor_averages.length: " + neighbor_averages.length);
																	final_average = final_average / neighbor_averages.length;
																	//context.log("final_average: "+final_average);
																	//context.log("final_average: "+final_average + ", parseFloat(PR):" + parseFloat(PR) + "=> "+ (parseFloat(PR) + final_average) );
																	//context.log(parseFloat(PR) + final_average);
																	final_avegare_of_prediction += (parseFloat(PR) + final_average);
																	//context.done();
																	//return true;
																});

																final_avegare_of_prediction = final_avegare_of_prediction/(for_last_n_minutes+1);
																context.log("We predict the average of system in next '"+for_last_n_minutes+"' minutes will be: " + final_avegare_of_prediction);

																if (final_avegare_of_prediction <= 50)
																{context.log(current_api + "&task=remove_resource");
																	//we should remove resource
																	req_handler_https.get(current_api + "&task=remove_resource", (resp) => {
																		let data = '';

																	// A chunk of data has been recieved.
																	resp.on('data', (chunk) => {
																		data += chunk;
																	});
																		
																		// The whole response has been received. Print out the result.
																		resp.on('end', () => {
																			context.log("'Decrease resource' request has been sent.");
																		context.done();
																	});

																	}).on("error", (err) => {
																			context.log("'Decrease resource' request has been failed. response code: " + err.message);
																		context.done();
																	});
																}
																else if (70 < final_avegare_of_prediction)
																{context.log(current_api + "&task=add_resource");
																	//we need to add resource
																	req_handler_https.get(current_api + "&task=add_resource", (resp) => {
																		let data = '';

																	// A chunk of data has been recieved.
																	resp.on('data', (chunk) => {
																		data += chunk;
																	});
																		
																		// The whole response has been received. Print out the result.
																		resp.on('end', () => {
																			context.log("'Increase resource' request has been sent.");
																		context.done();
																	});

																	}).on("error", (err) => {
																			context.log("'Increase resource' request has been failed. response code: " + err.message);
																		context.done();
																	});
																}
																
																context.done();
															}
														});
												}
												else {
													// Blob doesn't exist
													context.log("'"+dataset_blobName+"' doesn't exist. you should call 'build_model' task first. it will create '"+dataset_blobName+"' automatically");
													context.done();
												}
											});

										//###########################
										//## Load Original Dataset ##
										//###########################
										//context.log(predicted_results); //all predict_data_array_arg are requested
										//context.done();
									});

								}).on("error", (err) => {
										context.log("Error: " + err.message);
									reject(err);
									//return false;
								});
								return false;
								var predicted_results = [];


								//context.log(predict_data_array);
								//context.done();
							}, function(err) {
								context.log(err);
							});
						}
					});
				}
				else {
					// Blob doesn't exist
					context.log("'"+ML_model_config_file_name+"' doesn't exist. you should call 'build_model' task first. it will create '"+ML_model_config_file_name+"' automatically");
					context.done();
				}
			});
        }
		else if (task == 'ndbench_auto_limit') {
			var limitation_status = 'no_status';
			if (req.query.limitation_status || (req.body && req.body.limitation_status)) {
                limitation_status = req.query.limitation_status ? req.query.limitation_status : req.body.limitation_status;
            }
			
            if (limitation_status == 'start' || limitation_status == 'stop') {
				if (limitation_status == 'start')
				{
					//Act related to limitation_status
					var select_limit = Math.floor(Math.random() * 3);
					
					var readRateLimit = 1;
					var writeRateLimit = 1;
					
					var limits = ["Low", "Normal", "High"];
					
					var new_limit = limits[select_limit];
					
					var readRateLimit = Math.floor(Math.random() * 2000) + 1;
					var writeRateLimit = Math.floor(Math.random() * 2000) + 1;
					
					if (new_limit == "Normal") {
						readRateLimit = Math.floor(Math.random() * (9000 - 2000) ) + 2000;
						writeRateLimit = Math.floor(Math.random() * (9000 - 2000) ) + 2000;
					}
					else if (new_limit == "High") {
						readRateLimit = Math.floor(Math.random() * (12001 - 9000) ) + 9000;
						writeRateLimit = Math.floor(Math.random() * (12001 - 9000) ) + 9000;
					}
					
					var request = require('request');
					
					var options = {
						uri: NdbenchAPI+"REST/ndbench/config/set",
						method: 'POST',
						json: {'readRateLimit': readRateLimit, 'writeRateLimit': writeRateLimit}
					};

					request(options, function (error, response, body) {
						if (!error && response.statusCode == 200) {
							// Print out the response body
							context.log(body);
						}
						else
						{
							context.log('error =>', error);
						}
					});
					
					context.log(`New limit is '${new_limit}' => readRateLimit: '${readRateLimit}', writeRateLimit:'${writeRateLimit}'`);
					//context.done();
				}
				
				//Start Loading blob_database.json
                //Check to see if it is exists
                //#########################################
                //## Create Blob Container if not exists ##
                //#########################################
                var promise = new Promise(function(resolve, reject) {
                    blobService.createContainerIfNotExists(containerName, { publicAccessLevel: 'blob' }, err => {
                        if(err)
						{
                            context.log('Something is wrong with creating Blob Container:');
                            context.log(err);
                            reject(Error(err));
                            context.done();
                        }
						else
						{
                            //#############################
                            //## Blob container is ready ##
                            //#############################
                            context.log({ message: `Container '${containerName}' created` });
							resolve("Stuff worked!");

							var database = {};
							
							blobService.getBlobProperties(
							containerName,
							blob_database,
							function (err, properties, status) {
								if (status.isSuccessful) {
									// Blob exists
									context.log("Start loading '" + blob_database + "'.");
									blobService.getBlobToText(
										containerName,
										blob_database,
										function (err, blobContent, blob) {
											if (err) {
												context.error("Couldn't download blob %s", blob_database);
												context.error(err);
												context.done();
												return false;
											}
											else {
												context.log("Sucessfully downloaded blob %s", blob_database);
												var loaded_database = blobContent;
											   // context.log(loaded_database);
												if (loaded_database) {
													loaded_database = JSON.parse(loaded_database);
													//context.log(loaded_database);
													database = loaded_database;
												}
												else
												{
													context.log(`'${blob_database}' is not exists.`);
												}
												
												database.ndbench_auto_limit = limitation_status;
												
												context.log(`ndbench_auto_limit being set to '${limitation_status}'.`);
												upload_to_blob(blobService, containerName, blob_database, JSON.stringify(database));

												context.done();
											}
											//context.done();
										});
								}
								else {
									// Blob doesn't exist
									context.log("'" + blob_database + "' doesn't exist.");

									//Start creating new one
									var database = {};
									database.ndbench_auto_limit = limitation_status;
									
									upload_to_blob(blobService, containerName, blob_database, JSON.stringify(database));

									context.done();
									return false;
								}
							});
						}
					});
					
                    //context.done();
                });
				
            }
            else {
				//there is no status in the request. we won't do anything
				context.log("if you don't send 'limitation_status' with your request, nothing will happen for ndbebench automation.");
                context.done();
            }
		}
    }
    else
    {
        context.res = {
            status: 400,
            body: "Please pass a task on the query string or in the request body"
        };
        context.done();
    }
	
	function get_metrics (start_time, end_time, callback)
	{
		const memory_query = grafana_API + 'avg ((node_memory_MemTotal_bytes-node_memory_MemFree_bytes-node_memory_Cached_bytes)/(node_memory_MemTotal_bytes)*100)&start='+start_time+'&end='+end_time+'&step=60';
		//const cpu_query = grafana_API + 'avg (100 - (avg by (instance) (irate(node_cpu{name="node-exporter",mode="idle"}[5m])) * 100))&start='+start_time+'&end='+end_time+'&step=60';
		const cpu_query = grafana_API + 'avg (100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100))&start='+start_time+'&end='+end_time+'&step=60';
		//const network_in = grafana_API + 'avg(container_network_receive_bytes_total)&start='+(start_time - 60)+'&end='+end_time+'&step=60';
		const network_in = grafana_API + 'avg(node_network_receive_bytes_total)&start='+(start_time - 60)+'&end='+end_time+'&step=60';
		//const network_out = grafana_API + 'avg(container_network_transmit_bytes_total)&start='+(start_time - 60)+'&end='+end_time+'&step=60';
		const network_out = grafana_API + 'avg(node_network_transmit_bytes_total)&start='+(start_time - 60)+'&end='+end_time+'&step=60';
		
		let collected_metrics = {};
		return new Promise(function(resolve, reject) {
			req_handler.get(memory_query, (resp) => {
				let data = '';

				// A chunk of data has been recieved.
				resp.on('data', (chunk) => {
					data += chunk;
				});

				// The whole response has been received. Print out the result.
				resp.on('end', () => {
					//############
					//## MEMORY ##
					//############
					let json_response = JSON.parse(data);
					collected_metrics.memory = json_response.data.result[0].values;
					context.log("## MEMORY data has been received ##");

					req_handler.get(cpu_query, (resp) => {
						let data = '';

						// A chunk of data has been recieved.
						resp.on('data', (chunk) => {
							data += chunk;
						});

						// The whole response has been received. Print out the result.
						resp.on('end', () => {
							//#########
							//## CPU ##
							//#########
                            
							let json_response = JSON.parse(data);
							collected_metrics.cpu = json_response.data.result[0].values;
							context.log("## CPU data has been received ##");
							//context.log(collected_metrics);
							
							req_handler.get(network_in, (resp) => {
								let data = '';

								// A chunk of data has been recieved.
								resp.on('data', (chunk) => {
									data += chunk;
								});

								// The whole response has been received. Print out the result.
								resp.on('end', () => {
									//################
									//## NETWORK IN ##
									//################
                                    
									let json_response = JSON.parse(data);
									collected_metrics.network_in = json_response.data.result[0].values;
									context.log("## NETWORK IN data has been received ##");
									//context.log(collected_metrics);

									req_handler.get(network_out, (resp) => {
										let data = '';

										// A chunk of data has been recieved.
										resp.on('data', (chunk) => {
											data += chunk;
										});

										// The whole response has been received. Print out the result.
										resp.on('end', () => {
											//#################
											//## NETWORK OUT ##
											//#################
											let json_response = JSON.parse(data);
											collected_metrics.network_out = json_response.data.result[0].values;
											context.log("## NETWORK OUT data has been received ##");
											
											resolve(collected_metrics);
											//return collected_metrics;
											
											/*context.res = {
												// status: 200, // Defaults to 200
												body: JSON.stringify(final_output),
												headers: {
													'Content-Type': 'text/plain'
												}
											};

											//context.log(temp_output);
											
											context.done();*/
										});

									}).on("error", (err) => {
										context.log("Error: " + err.message);
										reject(err);
										//return false;
									});
								});

							}).on("error", (err) => {
								context.log("Error: " + err.message);
								reject(err);
								//return false;
							});
							
						});

					}).on("error", (err) => {
						context.log("Error: " + err.message);
						reject(err);
						//return false;
					});

				});

			}).on("error", (err) => {
				context.log("Error: " + err.message);
				reject(err);
				//return false;
			});
		 
		});

		
	}

	function normilize (collected_metrics)
	{
		context.log("## Convert collected metrics to JSON FORMAT and make timestamp Readable by human ##");
		let temp_output = {};
		let final_output = {};
		collected_metrics.memory.forEach(function(value, index) {
			var date = new Date(parseInt(value[0]) * 1000);
			var temp_date = date.getFullYear() + "-" + (date.getMonth() + 1) + "-" + date.getDate();
			var temp_time = date.getHours() + ":" + date.getMinutes();
			
			var query_time = date.getFullYear()+"_"+(date.getMonth() + 1)+"_"+date.getDate()+"_"+date.getHours()+"_"+date.getMinutes();
			if (typeof temp_output[query_time] == "undefined")
			{
				temp_output[query_time] = {};
				final_output[query_time] = {}
			}
			
			//################################################
			//Network is Aggregated then we should solve this problem
			//Maximum Network capability is 500Mbps = 62.5MBps
			//read more about capabilities:
			//https://www.vioreliftode.com/index.php/what-does-microsoft-mean-by-low-moderate-high-very-high-extremely-high-azure-network-bandwidth-part-1/
			//################################################
			if (
			typeof collected_metrics.network_in[index+1][1] != "undefined" &&
			typeof collected_metrics.network_in[index][1] != "undefined" &&
			typeof collected_metrics.network_out[index+1][1] != "undefined" &&
			typeof collected_metrics.network_out[index][1] != "undefined" &&
			typeof collected_metrics.cpu[index][1] != "undefined" &&
			typeof collected_metrics.memory[index][1] != "undefined"
			)
			{
				let network_in = Math.abs(parseFloat(((collected_metrics.network_in[index+1][1]) - parseFloat(collected_metrics.network_in[index][1])) / 1024));
				let network_out = Math.abs(parseFloat(((collected_metrics.network_out[index+1][1]) - parseFloat(collected_metrics.network_out[index][1])) / 1024));
				
				temp_output[query_time].date = temp_date;
				temp_output[query_time].time = temp_time;
				temp_output[query_time].original_network_in = network_in;//parseFloat(collected_metrics.network_in[index][1]);
				temp_output[query_time].original_network_out = network_out;//parseFloat(collected_metrics.network_out[index][1]);
				temp_output[query_time].network_in = (network_in * 100) / 640000;
				temp_output[query_time].network_out = (network_out * 100) / 640000;
				temp_output[query_time].cpu = parseFloat(collected_metrics.cpu[index][1]);
				temp_output[query_time].memory = parseFloat(value[1]);

				final_output[query_time].date = temp_date;
				final_output[query_time].time = temp_time;
				final_output[query_time].network_in = network_in;
				final_output[query_time].network_out = network_out;
				final_output[query_time].cpu = temp_output[query_time].cpu;
				final_output[query_time].memory = temp_output[query_time].memory;
			}
		});

		//#############################
		//Calculate Sum for each metric
		//#############################
		let cpu_total_sum = 0
		let memory_total_sum = 0
		let network_in_total_sum = 0
		let network_out_total_sum = 0

		for (var key in temp_output) {
			cpu_total_sum += temp_output[key].cpu;
			memory_total_sum += temp_output[key].memory;
			network_in_total_sum += temp_output[key].network_in;
			network_out_total_sum += temp_output[key].network_out;
		}

		let total_sum = cpu_total_sum + memory_total_sum + network_in_total_sum + network_out_total_sum;

		let normilized_json = {};
		let cpu_sum_of_LNs = 0;
		let memory_sum_of_LNs = 0;
		let network_in_sum_of_LNs = 0;
		let network_out_sum_of_LNs = 0;

		for (var key in temp_output) {
			if (typeof normilized_json[key] == "undefined")
			{
				normilized_json[key] = {};
			}

			var temp = (temp_output[key].cpu/100)/total_sum;
			if (temp == 0)
			{
				temp = 0.0000001;
			}
			//context.log(total_sum);
			//context.log(temp_output[key].cpu);
			//context.log(temp);
			//context.log(Math.log(temp));
			//context.log("====");

			temp = temp * Math.log(temp);
			normilized_json[key].cpu = temp;
			cpu_sum_of_LNs += temp;

			temp = (temp_output[key].memory/100)/total_sum;
			if (temp == 0)
			{
				temp = 0.0000001;
			}

			temp = temp * Math.log(temp);
			normilized_json[key].memory = temp;
			memory_sum_of_LNs += temp;

			temp = (temp_output[key].network_in/100)/total_sum;
			if (temp == 0)
			{
				temp = 0.0000001;
			}

			temp = temp * Math.log(temp);
			normilized_json[key].network_in = temp;
			network_in_sum_of_LNs += temp;

			temp = (temp_output[key].network_out/100)/total_sum;
			if (temp == 0)
			{
				temp = 0.0000001;
			}

			temp = temp * Math.log(temp);
			normilized_json[key].network_out = temp;
			network_out_sum_of_LNs += temp;
		}

		//context.log(JSON.stringify(normilized_json));

		let weights = {};
		let k = 1 / Math.log(Object.keys(normilized_json).length);
		let cpu_entropy = cpu_sum_of_LNs * (-1 * k);
		let memory_entropy = memory_sum_of_LNs * (-1 * k);
		let network_in_entropy = network_in_sum_of_LNs * (-1 * k);
		let network_out_entropy = network_out_sum_of_LNs * (-1 * k);
		
		
		let sum_of_entropies = cpu_entropy + memory_entropy + network_in_entropy + network_out_entropy;
		
		weights.cpu = cpu_entropy / sum_of_entropies;
		weights.memory = memory_entropy / sum_of_entropies;
		weights.network_in = network_in_entropy / sum_of_entropies;
		weights.network_out = network_out_entropy / sum_of_entropies;

		for (var key in temp_output)
		{
			let temp_final_target =
			temp_output[key].cpu * weights.cpu +
			temp_output[key].memory * weights.memory + 
			temp_output[key].network_in * weights.network_in + 
			temp_output[key].network_out * weights.network_out;

			let final_target_class = 1; //Low
			if (45 < temp_final_target && temp_final_target <= 60)
			{
				final_target_class = 2; //Normal
			}
			else if (60 < temp_final_target)
			{
				final_target_class = 3; //High
			}

			temp_output[key].final_target = temp_final_target;
			temp_output[key].final_class = final_target_class;

			final_output[key].final_target = temp_final_target;
			final_output[key].final_class = final_target_class;
		}
		
		return final_output;
	}

    function upload_to_blob(blobService, containerName, blob_name, blob_string) {
        //#####################
        //## Start Uploading ##
        //#####################
        blobService.createBlockBlobFromText(
            containerName,
            blob_name,
            blob_string,
            function (error, result, response) {
                if (error) {
                    context.log(`Couldn't upload ${blob_name}`);
                    context.error(error);
                    //context.done();
                    return false;
                }
                else {
                    context.log(`${blob_name} uploaded successfully`);
                    return true;
                }
            });
    }

	function upload_dataset (normilized_dataset, callback)
	{
		let dataset_string = 'date,time,cpu,memory,network_in,network_out,final_target,final_class\r\n';
		for (var key in normilized_dataset)
		{
			dataset_string += normilized_dataset[key].date+","+ normilized_dataset[key].time+","+ normilized_dataset[key].cpu+","+ normilized_dataset[key].memory+","+ normilized_dataset[key].network_in+","+ normilized_dataset[key].network_out+","+ normilized_dataset[key].final_target+","+ normilized_dataset[key].final_class+"\r\n"; 
		}
		
		//const sourceFilePath = path.resolve('./example.txt');
		//const dataset_blobName = path.basename(sourceFilePath, path.extname(sourceFilePath));

        let dataset_config = '';
		return new Promise(function(resolve, reject) {
            //#########################################
            //## Create Blob Container if not exists ##
            //#########################################
            blobService.createContainerIfNotExists(containerName, { publicAccessLevel: 'blob' }, err => {
                if(err) {
                    context.log('Something is wrong with creating Blob Container:');
                    context.log(err);
                } else {
                    //#############################
                    //## Blob container is ready ##
                    //#############################
                    context.log({ message: `Container '${containerName}' created` });

                    //#####################
                    //## Start Uploading ##
                    //#####################
                    blobService.createBlockBlobFromText(
                    containerName,
                    dataset_blobName,
                    dataset_string,
                    function(error, result, response)
                    {
                        if(error)
                        {
                            context.log("Couldn't upload string");
                            context.error(error);
                            context.done();
                            return false;
                        }
                        else
                        {
                            context.log('File uploaded successfully');
                            //uploaded file url is like this:
                            //https://testresourcegroup234.blob.core.windows.net/test-container/dataset.csv
                            //we should create configuration file and upload it and send it to ML_API to start creating model
							//dataset_config_file_name = 'dataset_config.json';
                            dataset_config = '{"type": "csv", "name": "'+dataset_blobName+'", "url":"https://'+storage_account_name+'.blob.core.windows.net/'+containerName+'/'+dataset_blobName+'", "has_header_row": "yes", "train_columns": [{"col_name": "cpu", "col_number": "2"}, {"col_name": "memory", "col_number": "3"}, {"col_name": "network_in", "col_number": "4"}, {"col_name": "network_out", "col_number": "5"}], "multiclass_target_col": {"col_name": "final_class", "col_number": "7"}, "regression_target_col": {"col_name": "final_target", "col_number": "6"}, "export_model_name": "ski_model"}';
                            
                            //#################################
                            //## Start Uploading Config File ##
                            //#################################
                            blobService.createBlockBlobFromText(
                            containerName,
                            dataset_config_file_name,
                            dataset_config,
                            function(error2, result2, response2)
                            {
                                if(error2)
                                {
                                    context.log("Couldn't upload config string");
                                    context.error(error2);
                                    context.done();
                                    return false;
                                }
                                else
                                {
                                    context.log('Config File uploaded successfully');
									//uploaded file url is like this:
									//https://testresourcegroup234.blob.core.windows.net/test-container/dataset_config.json
									//we should return this url
                                    //callback(dataset_config);
                                    resolve("https://"+storage_account_name+".blob.core.windows.net/"+containerName+"/"+dataset_config_file_name);
                                }
                            });
                        }
                    });

                    //context.done();
                }
            });
        });
		
		
	}
};
