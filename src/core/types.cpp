/*  Copyright (C) 2014-2016 FastoGT. All right reserved.

    This file is part of FastoNoSQL.

    FastoNoSQL is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    FastoNoSQL is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with FastoNoSQL.  If not, see <http://www.gnu.org/licenses/>.
*/

#include "core/types.h"

#include <vector>
#include <string>

#include "common/string_util.h"
#include "common/sprintf.h"

namespace fastonosql {
namespace core {

CommandInfo::CommandInfo(const std::string& name, const std::string& params,
                         const std::string& summary, uint32_t since,
                         const std::string& example, uint8_t required_arguments_count,
                         uint8_t optional_arguments_count)
  : name(name), params(params), summary(summary), since(since), example(example),
    required_arguments_count(required_arguments_count),
    optional_arguments_count(optional_arguments_count) {
}

uint16_t CommandInfo::maxArgumentsCount() const {
  return required_arguments_count + optional_arguments_count;
}

uint8_t CommandInfo::minArgumentsCount() const {
  return required_arguments_count;
}

CommandHolder::CommandHolder(const std::string& name, const std::string& params,
                             const std::string& summary, uint32_t since,
                             const std::string& example, uint8_t required_arguments_count,
                             uint8_t optional_arguments_count, function_type func)
  : CommandInfo(name, params, summary, since, example,
                required_arguments_count, optional_arguments_count), func_(func){
}

bool CommandHolder::isCommand(const std::string& cmd) {
  return FullEqualsASCII(cmd, name, false);
}

common::Error CommandHolder::execute(CommandHandler *handler, int argc, char** argv, FastoObject* out) {
  return func_(handler, argc, argv, out);
}

CommandHandler::CommandHandler(const std::vector<commands_t> &commands)
  : commands_(commands) {
}

common::Error CommandHandler::execute(int argc, char** argv, FastoObject* out) {
  char * input_cmd = argv[0];
  for(size_t i = 0; i < commands_.size(); ++i) {
    commands_t cmd = commands_[i];
    if (cmd.isCommand(input_cmd)) {
      int argc_to_call = argc - 1;
      char** argv_to_call = argv + 1;
      if (argc_to_call > cmd.maxArgumentsCount() || argc_to_call < cmd.minArgumentsCount()) {
        std::string buff = common::MemSPrintf("Invalid input argument for command: %s", input_cmd);
        return common::make_error_value(buff, common::ErrorValue::E_ERROR);
      }

      return cmd.execute(this, argc_to_call, argv_to_call, out);
    }
  }

  return notSupported(input_cmd);
}

common::Error CommandHandler::notSupported(const char* cmd) {
  std::string buff = common::MemSPrintf("Not supported command: %s", cmd);
  return common::make_error_value(buff, common::ErrorValue::E_ERROR);
}

std::string convertVersionNumberToReadableString(uint32_t version) {
  if (version != UNDEFINED_SINCE) {
    return common::convertVersionNumberToString(version);
  }

  return UNDEFINED_SINCE_STR;
}

ServerDiscoveryInfo::ServerDiscoveryInfo(connectionTypes ctype, serverTypes type, bool self)
  : host_(), name_(), self_(self), type_(type), ctype_(ctype) {
}

connectionTypes ServerDiscoveryInfo::connectionType() const {
  return ctype_;
}

serverTypes ServerDiscoveryInfo::type() const {
  return type_;
}

bool ServerDiscoveryInfo::self() const {
  return self_;
}

std::string ServerDiscoveryInfo::name() const {
  return name_;
}

void ServerDiscoveryInfo::setName(const std::string& name) {
  name_ = name;
}

common::net::hostAndPort ServerDiscoveryInfo::host() const {
  return host_;
}

void ServerDiscoveryInfo::setHost(const common::net::hostAndPort& host) {
  host_ = host;
}


ServerDiscoveryInfo::~ServerDiscoveryInfo() {
}

IServerInfo::~IServerInfo() {
}

connectionTypes IServerInfo::type() const {
  return type_;
}

IServerInfo::IServerInfo(connectionTypes type)
  : type_(type) {
}

Field::Field(const std::string& name, common::Value::Type type)
  : name(name), type(type) {
}

bool Field::isIntegral() const {
  return common::Value::isIntegral(type);
}

std::vector<common::Value::Type> supportedTypesFromType(connectionTypes type) {
#ifdef BUILD_WITH_REDIS
  if (type == REDIS) {
    return DBTraits<REDIS>::supportedTypes();
  }
#endif
#ifdef BUILD_WITH_MEMCACHED
  if (type == MEMCACHED) {
    return DBTraits<MEMCACHED>::supportedTypes();
  }
#endif
#ifdef BUILD_WITH_SSDB
  if (type == SSDB) {
    return DBTraits<SSDB>::supportedTypes();
  }
#endif
#ifdef BUILD_WITH_LEVELDB
  if (type == LEVELDB) {
    return DBTraits<LEVELDB>::supportedTypes();
  }
#endif
#ifdef BUILD_WITH_ROCKSDB
  if (type == ROCKSDB) {
    return DBTraits<ROCKSDB>::supportedTypes();
  }
#endif
#ifdef BUILD_WITH_UNQLITE
  if (type == UNQLITE) {
    return DBTraits<UNQLITE>::supportedTypes();
  }
#endif
#ifdef BUILD_WITH_LMDB
  if (type == LMDB) {
    return DBTraits<LMDB>::supportedTypes();
  }
#endif
  NOTREACHED();
  return std::vector<common::Value::Type>();
}

std::vector<std::string> infoHeadersFromType(connectionTypes type) {
#ifdef BUILD_WITH_REDIS
  if (type == REDIS) {
    return DBTraits<REDIS>::infoHeaders();
  }
#endif
#ifdef BUILD_WITH_MEMCACHED
  if (type == MEMCACHED) {
    return DBTraits<MEMCACHED>::infoHeaders();
  }
#endif
#ifdef BUILD_WITH_SSDB
  if (type == SSDB) {
    return DBTraits<SSDB>::infoHeaders();
  }
#endif
#ifdef BUILD_WITH_LEVELDB
  if (type == LEVELDB) {
    return DBTraits<LEVELDB>::infoHeaders();
  }
#endif
#ifdef BUILD_WITH_ROCKSDB
  if (type == ROCKSDB) {
    return DBTraits<ROCKSDB>::infoHeaders();
  }
#endif
#ifdef BUILD_WITH_UNQLITE
  if (type == UNQLITE) {
    return DBTraits<UNQLITE>::infoHeaders();
  }
#endif
#ifdef BUILD_WITH_LMDB
  if (type == LMDB) {
    return DBTraits<LMDB>::infoHeaders();
  }
#endif
  NOTREACHED();
  return std::vector<std::string>();
}

std::vector< std::vector<Field> > infoFieldsFromType(connectionTypes type) {
#ifdef BUILD_WITH_REDIS
  if (type == REDIS) {
    return DBTraits<REDIS>::infoFields();
  }
#endif
#ifdef BUILD_WITH_MEMCACHED
  if (type == MEMCACHED) {
    return DBTraits<MEMCACHED>::infoFields();
  }
#endif
#ifdef BUILD_WITH_SSDB
  if (type == SSDB) {
    return DBTraits<SSDB>::infoFields();
  }
#endif
#ifdef BUILD_WITH_LEVELDB
  if (type == LEVELDB) {
    return DBTraits<LEVELDB>::infoFields();
  }
#endif
#ifdef BUILD_WITH_ROCKSDB
  if (type == ROCKSDB) {
    return DBTraits<ROCKSDB>::infoFields();
  }
#endif
#ifdef BUILD_WITH_UNQLITE
  if (type == UNQLITE) {
    return DBTraits<UNQLITE>::infoFields();
  }
#endif
#ifdef BUILD_WITH_LMDB
  if (type == LMDB) {
    return DBTraits<LMDB>::infoFields();
  }
#endif
  NOTREACHED();
  return std::vector<std::vector<Field>>();
}

ServerInfoSnapShoot::ServerInfoSnapShoot()
  : msec(0), info() {
}

ServerInfoSnapShoot::ServerInfoSnapShoot(common::time64_t msec, IServerInfoSPtr info)
  : msec(msec), info(info) {
}

bool ServerInfoSnapShoot::isValid() const {
  return msec > 0 && info;
}

IDataBaseInfo::IDataBaseInfo(const std::string& name, bool isDefault, connectionTypes type,
                           size_t size, const keys_container_t& keys)
  : name_(name), is_default_(isDefault), type_(type), size_(size), keys_(keys) {
}

IDataBaseInfo::~IDataBaseInfo() {
}

connectionTypes IDataBaseInfo::type() const {
  return type_;
}

std::string IDataBaseInfo::name() const {
  return name_;
}

size_t IDataBaseInfo::sizeDB() const {
  return size_;
}

void IDataBaseInfo::setSizeDB(size_t size) {
  size_ = size;
}

size_t IDataBaseInfo::loadedSize() const {
  return keys_.size();
}

bool IDataBaseInfo::isDefault() const {
  return is_default_;
}

void IDataBaseInfo::setIsDefault(bool isDef) {
  is_default_ = isDef;
}

void IDataBaseInfo::setKeys(const keys_container_t& keys) {
  keys_ = keys;
}

void IDataBaseInfo::clearKeys() {
  keys_.clear();
}

IDataBaseInfo::keys_container_t IDataBaseInfo::keys() const {
  return keys_;
}

}  // namespace core
}  // namespace fastonosql
