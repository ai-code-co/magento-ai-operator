# backend/app/services/magento_wrapper.py
import requests
import urllib.parse
from requests_oauthlib import OAuth1
import re

class MagentoService:
    def _make_request(self, method: str, endpoint: str, credentials: dict, query_params: str = ""):
        if not credentials: raise ValueError("Magento credentials are required.")
        base_url = credentials['store_url'].rstrip('/')
        full_request_url = f"{base_url}/index.php/rest/V1{endpoint}{query_params}"
        print("full request url 12",full_request_url)
        
        auth = OAuth1(client_key=credentials['consumer_key'], client_secret=credentials['consumer_secret'], resource_owner_key=credentials['access_token'], resource_owner_secret=credentials['access_token_secret'], signature_method='HMAC-SHA256')
        try:
            response = requests.request(method, full_request_url, auth=auth, headers={'Content-Type': 'application/json'})
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_message = e.response.json().get("message", e.response.reason) if e.response.text else e.response.reason
            raise Exception(f"Magento API Error: {e.response.status_code} - {error_message}")

    def _get_brand_id(self, brand_name: str, credentials: dict) -> str | None:
        attribute_code_for_brand = "manufacturer"
        endpoint = f"/products/attributes/{attribute_code_for_brand}/options"
        try:
            options = self._make_request("GET", endpoint, credentials)
            print("28 options",options)
            if isinstance(options, list):
                for option in options:
                    if isinstance(option, dict) and option.get('label', '').strip().lower() == brand_name.strip().lower():
                        return option.get('value')
            return None
        except Exception as e:
            print(f"INFO: Could not get brand options for '{brand_name}', will fall back to text search. Error: {e}")
            return None

    def _get_category_id(self, category_name: str, credentials: dict) -> str | None:
        """
        Hits /V1/categories/list to find the ID for a given name.
        """
        endpoint = "/categories/list"
        encoded_name = urllib.parse.quote(category_name)
        
        
        # query_string = (
        #     f"searchCriteria[filter_groups][0][filters][0][field]=name&"
        #     f"searchCriteria[filter_groups][0][filters][0][value]=%{encoded_name}%&"
        #     f"searchCriteria[filter_groups][0][filters][0][condition_type]=like"
        # )
        query_string =f"searchCriteria[filter_groups][0][filters][0][field]=name&searchCriteria[filter_groups][0][filters][0][value]=%{encoded_name}%& searchCriteria[filter_groups][0][filters][0][condition_type]=like"
        
        
        try:
            response = self._make_request("GET", endpoint, credentials, query_params=f"?{query_string}")
            items = response.get('items', [])
            # print("54 items",items)
            if items:
                return items[0].get('id')
            return None
        except Exception as e:
            print(f"INFO: Could not resolve category '{category_name}': {e}")
            return None
    
    
    def find_categories_by_name(self,category_node, target_name, results=None):
        """
        Recursively search Magento category tree for categories
        whose name matches target_name.
        :param category_node: dict (single category node)
        :param target_name: str (name to search)
        :param results: list (used internally for recursion)
        :return: list of matching category dicts
        """
        if results is None:
            results = []
            
        name = category_node.get("name")    
        # Case-insensitive comparison
        if isinstance(name, str) and name.lower() == target_name.lower():
            results.append(category_node)

        #Recurse through children
        for child in category_node.get("children_data", []):
            self.find_categories_by_name(category_node=child, target_name=target_name, results=results)
        return results
        
    def product_query(self, params: dict, credentials: dict) -> dict:
        print(f"UNIFIED QUERY with params: {params}")
        
        # --- CONFIGURATION: Attributes that require EXACT match to avoid substring errors ---
        # e.g., "2 Watt" matching "12 Watt"
        EXACT_MATCH_FIELDS = ['power', 'bulb_base', 'dimmable', 'technology', 'lamp_type', 'manufacturer', 'lumens']

        def build_query(use_fallback=False):
            query_parts = []
            filter_group_index = 0
            
            # 1. Category
            if params.get("category"):
                target_name = params["category"]
                try:
                    tree_data = self._make_request("GET", endpoint="/categories", credentials=credentials)
                    matches = self.find_categories_by_name(tree_data, target_name=target_name)
                    if matches:
                        category_node = matches[0]
                        category_id = category_node.get("id")
                        
                        if params.get("task") == "count" and not params.get("keywords") and not params.get("brand") and not params.get("on_sale"):
                            return "FAST_COUNT", category_node.get("product_count", 0)
                        
                        if category_id:
                            query_parts.append(f"searchCriteria[filter_groups][{filter_group_index}][filters][0][field]=category_id&searchCriteria[filter_groups][{filter_group_index}][filters][0][value]={category_id}&searchCriteria[filter_groups][{filter_group_index}][filters][0][condition_type]=eq")
                            filter_group_index += 1
                except Exception as e:
                    print(f"Error fetching category tree: {e}")

            # 2. SKU
            if params.get("sku"):
                encoded_sku = urllib.parse.quote(params["sku"])
                query_parts.append(f"searchCriteria[filter_groups][{filter_group_index}][filters][0][field]=sku&searchCriteria[filter_groups][{filter_group_index}][filters][0][value]={encoded_sku}&searchCriteria[filter_groups][{filter_group_index}][filters][0][condition_type]=eq")
                filter_group_index += 1

            # 3. Keywords / Attributes
            if params.get("keywords"):
               keywords_data = params["keywords"]
               if isinstance(keywords_data, str): keywords_data = {"name": keywords_data} 

               for key, value in keywords_data.items():
                   if use_fallback:
                       field_to_search = "name"
                       # Fallback always uses LIKE
                       condition_type = "like"
                       raw_val = f"%{value}%"
                   else:
                       if key in ['keywords', 'search', 'query']: 
                           field_to_search = "name"
                       else: 
                           field_to_search = key.lower().replace(" ", "_")
                       
                       # Check for Exact Match Requirement ---
                       if field_to_search in EXACT_MATCH_FIELDS:
                           condition_type = "eq"
                           raw_val = f"{value}" # No wildcards for exact match
                       else:
                           condition_type = "like"
                           raw_val = f"%{value}%" # Wildcards for partial match (Voltage, Name)
                   
                   encoded_val = urllib.parse.quote(raw_val)

                   query_parts.append(f"searchCriteria[filter_groups][{filter_group_index}][filters][0][field]={field_to_search}&searchCriteria[filter_groups][{filter_group_index}][filters][0][value]={encoded_val}&searchCriteria[filter_groups][{filter_group_index}][filters][0][condition_type]={condition_type}")
                   filter_group_index += 1

            # 4. Brand
            if params.get("brand"):
                brand_id = self._get_brand_id(params["brand"], credentials)
                if brand_id:
                    query_parts.append(f"searchCriteria[filter_groups][{filter_group_index}][filters][0][field]=manufacturer&searchCriteria[filter_groups][{filter_group_index}][filters][0][value]={brand_id}&searchCriteria[filter_groups][{filter_group_index}][filters][0][condition_type]=eq")
                    filter_group_index += 1
            
            # 5. On Sale
            if params.get("on_sale"):
                query_parts.append(f"searchCriteria[filter_groups][{filter_group_index}][filters][0][field]=special_price&searchCriteria[filter_groups][{filter_group_index}][filters][0][condition_type]=notnull")
                filter_group_index += 1

            # Pagination & Fields
            task = params.get("task", "search")
            limit = params.get("limit", 10) 
            
            if task == "count":
                query_parts.append("searchCriteria[pageSize]=0")
                query_parts.append("fields=total_count")
            else:
                query_parts.append(f"searchCriteria[pageSize]={limit}")
                query_parts.append("fields=items[id,sku,name,price,special_price,custom_attributes,media_gallery_entries[id,file,types]],total_count")

            return "QUERY", "&".join(query_parts)
        
        # EXECUTE 
        endpoint = "/products"
        
        result_type, query_string = build_query(use_fallback=False)
        
        if result_type == "FAST_COUNT": return {"total_count": query_string}

        try:
            print(f"Attempting Attribute Search: {query_string}")
            raw_result = self._make_request("GET", endpoint, credentials, query_params=f"?{query_string}")
        except Exception as e:
            if "400" in str(e) and "attribute name is invalid" in str(e):
                print("WARNING: Attribute search failed. Retrying with Name Fallback...")
                result_type, query_string = build_query(use_fallback=True)
                try:
                    raw_result = self._make_request("GET", endpoint, credentials, query_params=f"?{query_string}")
                except Exception as e2:
                    print(f"Fallback search also failed: {e2}")
                    return {"items": [], "total_count": 0}
            else:
                print(f"Search failed: {e}")
                return {"items": [], "total_count": 0}
        
        items = raw_result.get('items', []) if isinstance(raw_result, dict) else []
        if not isinstance(items, list): items = []
        total_count = raw_result.get('total_count', 0) if isinstance(raw_result, dict) else 0
            
        if params.get("task") == "count": return {"total_count": total_count}

        formatted_products = []
        for product in items:
            if not isinstance(product, dict): continue
            description = "No description available."
            description_html, short_description_html = "", ""
            custom_attrs = product.get('custom_attributes', [])
            if isinstance(custom_attrs, list):
                for attr in custom_attrs:
                    if not isinstance(attr, dict): continue
                    if attr.get('attribute_code') == 'short_description': short_description_html = attr.get('value', '')
                    if attr.get('attribute_code') == 'description': description_html = attr.get('value', '')
            final_html = short_description_html or description_html
            if final_html and isinstance(final_html, str):
                clean_desc = re.sub('<[^<]+?>', '', final_html); clean_desc = re.sub('&[a-zA-Z0-9]+;', ' ', clean_desc).strip()
                if clean_desc: description = clean_desc
            image_path = ""
            gallery = product.get('media_gallery_entries', [])
            if isinstance(gallery, list) and gallery:
                for entry in gallery:
                    if isinstance(entry, dict):
                        types = entry.get('types', [])
                        if isinstance(types, list) and 'image' in types: image_path = entry.get('file'); break
                if not image_path and gallery and isinstance(gallery[0], dict): image_path = gallery[0].get('file', '')
            display_price = "Price not available"
            try:
                special_price_val, price_val = product.get('special_price'), product.get('price')
                if special_price_val is not None and float(special_price_val) < float(price_val):
                    display_price = f"<del>${float(price_val):.2f}</del> <strong>${float(special_price_val):.2f}</strong>"
                elif price_val is not None:
                    display_price = f"${float(price_val):.2f}"
            except (ValueError, TypeError, AttributeError): pass
            formatted_products.append({"id": product.get('id'), "sku": product.get('sku'), "name": product.get('name'), "price": display_price, "image_url": f"{credentials['store_url'].rstrip('/')}/media/catalog/product{image_path}" if image_path else "", "description": description})
            
        return {"items": formatted_products, "total_count": total_count}
    def get_product_details_by_sku(self, sku: str, credentials: dict) -> dict | None:
        print(f"Getting full details for SKU: {sku}")
        try:
            safe_sku = urllib.parse.quote(sku, safe='')
            endpoint = f"/products/{safe_sku}"
            return self._make_request("GET", endpoint, credentials)
        except Exception as e:
            print(f"Error getting details for SKU {sku}: {e}")
            return None

magento_service = MagentoService()